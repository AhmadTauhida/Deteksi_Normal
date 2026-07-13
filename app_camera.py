import os
import sys

import cv2
from PySide6 import QtCore, QtGui, QtWidgets

from pose_tracker import AnkleTracker


class VideoThread(QtCore.QThread):
    # Signal mengekspektasikan QImage matang untuk dikirim ke UI Thread
    frame_ready = QtCore.Signal(QtGui.QImage, object, str)

    def __init__(self, tracker: AnkleTracker, source=0, parent=None):
        super().__init__(parent)
        self.tracker = tracker
        self.source = source
        self.running = False
        self.capture = None

    def run(self):
        import cv2
        import time

        print(f"[CAMERA DEBUG] Mencoba membuka source: {self.source}")
        
        # 1. Coba inisialisasi pertama sesuai source bawaan
        self.capture = cv2.VideoCapture(self.source)
        time.sleep(0.5)  # Jeda aman agar hardware USB siap

        # 2. AUTO-FALLBACK LOOP: Jika gagal terdeteksi, lakukan scanning otomatis dengan DirectShow backend
        if not self.capture.isOpened():
            print(f"[CAMERA DEBUG] Gagal membuka source {self.source}. Memulai pemindaian indeks alternatif...")
            
            # Daftar backend dan indeks yang akan dicoba secara otomatis (Utamakan DirectShow untuk Windows)
            alternative_sources = [
                0 + cv2.CAP_DSHOW,  # Indeks 0 dengan DirectShow (Windows)
                1 + cv2.CAP_DSHOW,  # Indeks 1 dengan DirectShow
                2 + cv2.CAP_DSHOW,  # Indeks 2 dengan DirectShow
                0, 1, 2, 3         # Indeks standar tanpa backend tambahan
            ]
            
            for alt_src in alternative_sources:
                if alt_src == self.source:
                    continue
                print(f"[CAMERA DEBUG] Mencoba indeks alternatif: {alt_src}")
                self.capture = cv2.VideoCapture(alt_src)
                time.sleep(0.4)
                if self.capture.isOpened():
                    print(f"[CAMERA DEBUG] BERHASIL! Kamera terhubung pada source: {alt_src}")
                    break
                else:
                    self.capture.release()

        # 3. Validasi akhir sebelum masuk ke loop rendering frame
        if self.capture.isOpened():
            self.capture.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
            self.capture.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)
            self.capture.set(cv2.CAP_PROP_BUFFERSIZE, 1)
            self.running = True
        else:
            print("[CAMERA DEBUG] ERROR: Seluruh indeks kamera gagal dibuka. Periksa izin privasi Windows atau kabel USB.")
            self.running = False

        # Loop pembacaan frame
        while self.running and self.capture.isOpened():
            success, frame = self.capture.read()
            if not success:
                print("[CAMERA DEBUG] Gagal membaca frame dari hardware.")
                break

            # Ekstraksi tracking dari MediaPipe
            processed_data, angle, side_label = self.tracker.process_frame(frame)
            
            # KOREKSI UTAMA: Pastikan output diubah ke QImage yang valid sebelum di-emit ke C++ PySide6
            if isinstance(processed_data, QtGui.QImage):
                q_image = processed_data
            elif processed_data is not None:
                try:
                    # Konversi array OpenCV BGR ke RGB
                    height, width, channel = processed_data.shape
                    bytes_per_line = channel * width
                    rgb_frame = cv2.cvtColor(processed_data, cv2.COLOR_BGR2RGB)
                    
                    # Bangun QImage dan gunakan .copy() agar memori aman di sisi C++
                    q_image = QtGui.QImage(
                        rgb_frame.data, 
                        width, 
                        height, 
                        bytes_per_line, 
                        QtGui.QImage.Format.Format_RGB888
                    ).copy()
                except Exception as e:
                    print(f"[CAMERA DEBUG] Gagal mengonversi matriks frame ke QImage: {str(e)}")
                    continue
            else:
                continue

            self.frame_ready.emit(q_image, angle, side_label)

        # Proses rilis hardware
        if self.capture is not None:
            self.capture.release()
            self.capture = None
            print("[CAMERA DEBUG] Hardware kamera berhasil dirilis secara aman.")


class AnkleCameraWidget(QtWidgets.QWidget):
    angle_updated = QtCore.Signal(object, str)

    def __init__(self, camera_source=0, embedded=False, parent=None):
        super().__init__(parent)
        self.camera_source = camera_source
        self.embedded = embedded
        self.tracker = AnkleTracker(model_complexity=1, smooth_landmarks=True)
        
        self.video_thread = None
        self._closing_threads = [] # List untuk menampung thread yang sedang proses penutupan (Anti-Crash)
        
        self._build_ui()
        
        if not self.embedded:
            self.start_camera()

    def _build_ui(self):
        layout = QtWidgets.QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)

        self.video_label = QtWidgets.QLabel("Kamera Belum Dimulai")
        self.video_label.setAlignment(QtCore.Qt.AlignmentFlag.AlignCenter)
        self.video_label.setStyleSheet("background-color: #E2E8F0; border-radius: 8px; color: #6B7A99; font-weight: bold;")
        self.video_label.setSizePolicy(QtWidgets.QSizePolicy.Policy.Expanding, QtWidgets.QSizePolicy.Policy.Expanding)
        layout.addWidget(self.video_label, stretch=1)

        if not self.embedded:
            self.angle_label = QtWidgets.QLabel("No ankle landmark visible")
            layout.addWidget(self.angle_label)
            
            self.status_label = QtWidgets.QLabel("Camera stopped")
            layout.addWidget(self.status_label)

    def handle_frame(self, image: QtGui.QImage, angle, side_label):
        if image.isNull():
            return
            
        pixmap = QtGui.QPixmap.fromImage(image)
        self.video_label.setPixmap(pixmap.scaled(
            self.video_label.width(),
            self.video_label.height(),
            QtCore.Qt.AspectRatioMode.KeepAspectRatio,
            QtCore.Qt.TransformationMode.SmoothTransformation
        ))

        if hasattr(self, 'angle_label'):
            if angle is None:
                self.angle_label.setText("No ankle landmark visible")
            else:
                self.angle_label.setText(f"{side_label} ankle angle: {angle:.1f}°")

        self.angle_updated.emit(angle, side_label)

    def start_camera(self):
        if self.video_thread is not None:
            self.stop_camera()

        self.video_thread = VideoThread(self.tracker, source=self.camera_source, parent=self)
        self.video_thread.frame_ready.connect(self.handle_frame)
        self.video_thread.start()
        
        if hasattr(self, 'status_label'):
            self.status_label.setText(f"Camera started (Source Index: {self.camera_source})")

    def stop_camera(self):
        """Menghentikan kamera secara asinkron tanpa membiarkan GC menghancurkan thread secara prematur."""
        if self.video_thread is not None:
            th = self.video_thread
            self.video_thread = None # Lepas kepemilikan dari widget
            th.running = False       # Beritahu loop OpenCV untuk berhenti
            
            # Simpan referensi thread ke list agar Python tidak melakukan Garbage Collect!
            self._closing_threads.append(th)
            
            # Buat callback untuk menghapus dari memori hanya SETELAH thread benar-benar mati
            def cleanup():
                if th in self._closing_threads:
                    self._closing_threads.remove(th)
                th.deleteLater()
                
            th.finished.connect(cleanup)

        # Ubah tampilan layar saat kamera dimatikan
        self.video_label.clear()
        self.video_label.setText("Kamera Dihentikan")

        if hasattr(self, 'status_label'):
            self.status_label.setText("Camera stopped")


def _run_standalone():
    app = QtWidgets.QApplication(sys.argv)
    window = QtWidgets.QMainWindow()
    window.setWindowTitle("Ankle Angle Detector (standalone)")
    window.setMinimumSize(900, 660)

    # Menempelkan widget langsung pada parent window agar tidak terhapus prematur oleh Garbage Collector
    window.camera_widget = AnkleCameraWidget(camera_source=0, embedded=False)
    window.setCentralWidget(window.camera_widget)

    def _closeEvent(event):
        window.camera_widget.stop_camera()
        import time
        time.sleep(0.3)  # Jeda aman melepaskan hardware link sebelum exit thread
        event.accept()

    window.closeEvent = _closeEvent
    window.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    _run_standalone()