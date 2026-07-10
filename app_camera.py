import os
import sys

import cv2
from PySide6 import QtCore, QtGui, QtWidgets

from pose_tracker import AnkleTracker


class VideoThread(QtCore.QThread):
    # Emits an already-processed QImage plus the computed angle/side label.
    # Doing the heavy work (MediaPipe inference) here, in the worker
    # thread, means the GUI thread only has to do a cheap QPixmap
    # conversion + label update in handle_frame().
    frame_ready = QtCore.Signal(QtGui.QImage, object, str)

    def __init__(self, tracker: AnkleTracker, source=1, parent=None):
        super().__init__(parent)
        self.tracker = tracker
        self.source = source
        self.running = False
        self.capture = None

    def run(self):
        self.capture = cv2.VideoCapture(self.source, cv2.CAP_DSHOW)
        self.capture.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
        self.capture.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)
        self.capture.set(cv2.CAP_PROP_BUFFERSIZE, 1)
        self.running = True

        while self.running and self.capture.isOpened():
            success, frame = self.capture.read()
            if not success:
                break

            image, angle, side_label = self.tracker.process_frame(frame)

            height, width = image.shape[:2]
            rgb_frame = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
            qimage = QtGui.QImage(
                rgb_frame.data,
                width,
                height,
                rgb_frame.strides[0],
                QtGui.QImage.Format.Format_RGB888,
            ).copy()

            self.frame_ready.emit(qimage, angle, side_label)

        if self.capture is not None:
            self.capture.release()
            self.capture = None

    def stop(self):
        self.running = False
        self.wait()


class AnkleCameraWidget(QtWidgets.QWidget):
    """Reusable ankle-angle camera widget.

    This used to be a standalone QMainWindow (MainWindow). It's now a plain
    QWidget so it can be embedded inside any frame/layout that another app
    (e.g. a teammate's GUI) already provides.

    Usage from another app:

        from app_camera import AnkleCameraWidget

        camera_widget = AnkleCameraWidget(camera_source=1, embedded=True)
        my_frame_layout.addWidget(camera_widget)
        camera_widget.start_camera()

        # in the HOST window's closeEvent:
        def closeEvent(self, event):
            camera_widget.stop_camera()
            super().closeEvent(event)

    IMPORTANT: because this is a plain QWidget (not a top-level window), its
    own closeEvent() will never fire when embedded, so the camera will keep
    running in the background unless the host app calls stop_camera()
    explicitly (e.g. in the host window's own closeEvent, or when the tab
    holding this widget is switched away, etc).
    """

    # Re-broadcast angle updates so the host app can react to them (e.g.
    # log data, drive a chart) without needing to touch this widget's
    # internals.
    angle_updated = QtCore.Signal(object, str)  # angle (float or None), side_label

    def __init__(self, camera_source: int = 1, embedded: bool = True, parent=None):
        super().__init__(parent)
        self.camera_source = camera_source
        self.embedded = embedded

        # One tracker instance is reused across camera restarts instead of
        # recreating the (heavy) MediaPipe Pose model every time. Safe
        # because only one VideoThread ever runs at a time.
        self.tracker = AnkleTracker()
        self.video_thread: QtCore.QThread | None = None

        self._build_ui()
        if not self.embedded:
            # Only load our own stylesheet when running standalone. When
            # embedded, the host app almost certainly wants its own
            # stylesheet applied to the whole window instead, so we stay
            # out of the way by default.
            self._load_stylesheet()

    def _build_ui(self):
        container = QtWidgets.QFrame(self)
        container.setObjectName("container")

        title_label = QtWidgets.QLabel("Real-Time Ankle Angle Detection", container)
        title_label.setObjectName("titleLabel")

        self.video_label = QtWidgets.QLabel(container)
        self.video_label.setObjectName("videoLabel")
        self.video_label.setFixedSize(760, 520)
        self.video_label.setAlignment(QtCore.Qt.AlignmentFlag.AlignCenter)

        self.angle_label = QtWidgets.QLabel("Waiting for camera...", container)
        self.angle_label.setObjectName("angleText")
        self.angle_label.setAlignment(QtCore.Qt.AlignmentFlag.AlignCenter)

        self.status_label = QtWidgets.QLabel(
            f"Camera source: Webcam {self.camera_source}", container
        )
        self.status_label.setObjectName("statusLabel")

        # NOTE: Restart/Stop buttons removed from here. Camera control is
        # now driven externally via start_camera()/stop_camera(), wired to
        # the integrated Start/Stop buttons in monitoring_page.py.
        layout = QtWidgets.QVBoxLayout(container)
        layout.addWidget(title_label)
        layout.addWidget(self.video_label)
        layout.addWidget(self.angle_label)
        layout.addWidget(self.status_label)

        outer_layout = QtWidgets.QVBoxLayout(self)
        outer_layout.setContentsMargins(0, 0, 0, 0)
        outer_layout.addWidget(container)

    def _load_stylesheet(self):
        style_path = os.path.join(os.path.dirname(__file__), "style.qss")
        if os.path.exists(style_path):
            with open(style_path, "r", encoding="utf-8") as stylesheet:
                self.setStyleSheet(stylesheet.read())

    def start_camera(self):
        """Public method so the host app decides exactly when the camera
        should turn on (e.g. only once this widget's tab/frame becomes
        visible), instead of it auto-starting on construction."""
        if self.video_thread is not None and self.video_thread.isRunning():
            return
        self.video_thread = VideoThread(self.tracker, source=self.camera_source)
        self.video_thread.frame_ready.connect(self.handle_frame)
        self.video_thread.start()
        self.status_label.setText(f"Camera started (Webcam {self.camera_source})")

    @QtCore.Slot(QtGui.QImage, object, str)
    def handle_frame(self, qimage, angle, side_label):
        self.video_label.setPixmap(QtGui.QPixmap.fromImage(qimage).scaled(
            self.video_label.width(),
            self.video_label.height(),
            QtCore.Qt.AspectRatioMode.KeepAspectRatio,
        ))

        if angle is None:
            self.angle_label.setText("No ankle landmark visible")
        else:
            self.angle_label.setText(f"{side_label} ankle angle: {angle:.1f}°")

        self.angle_updated.emit(angle, side_label)

    def stop_camera(self):
        """Public method the host app MUST call when this widget is being
        torn down (its own closeEvent won't fire when embedded)."""
        if self.video_thread is not None and self.video_thread.isRunning():
            self.video_thread.stop()
            self.status_label.setText("Camera stopped")


def _run_standalone():
    """Only used when running `python app_camera.py` directly for testing.
    Not used when a teammate imports AnkleCameraWidget into their own app."""
    app = QtWidgets.QApplication(sys.argv)

    window = QtWidgets.QMainWindow()
    window.setWindowTitle("Ankle Angle Detector (standalone)")
    window.setMinimumSize(900, 660)

    widget = AnkleCameraWidget(camera_source=1, embedded=False)
    window.setCentralWidget(widget)

    def _closeEvent(event, w=widget):
        w.stop_camera()
        QtWidgets.QMainWindow.closeEvent(window, event)

    window.closeEvent = _closeEvent

    window.show()
    widget.start_camera()
    sys.exit(app.exec())


if __name__ == "__main__":
    _run_standalone()