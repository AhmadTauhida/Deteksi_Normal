"""
widgets/camera_placeholder.py
Placeholder widget that mimics a live camera feed area.
"""

from PySide6.QtWidgets import QLabel, QVBoxLayout, QFrame, QWidget, QSizePolicy
from PySide6.QtCore import Qt, QTimer, QSize
from PySide6.QtGui import QPainter, QColor, QPen, QFont, QBrush, QPolygonF
from PySide6.QtCore import QPointF
import math


class CameraPlaceholder(QFrame):
    """
    A dark-themed placeholder resembling a camera feed area.
    Shows a pulsing "live" indicator and camera icon.
    """

    def __init__(self, parent=None):
        super().__init__(parent)
        self._running = False
        self._pulse = 0
        self._pulse_dir = 1

        self.setObjectName("Card")
        self.setMinimumSize(400, 300)
        self.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        self.setStyleSheet(
            "QFrame { background-color: #111827; border-radius: 14px; border: 2px solid #1E3A5F; }"
        )

        # Pulse timer for animation
        self._timer = QTimer(self)
        self._timer.timeout.connect(self._tick_pulse)
        self._timer.start(50)

    # ------------------------------------------------------------------
    def set_running(self, running: bool):
        self._running = running
        self.update()

    # ------------------------------------------------------------------
    def _tick_pulse(self):
        self._pulse += self._pulse_dir * 3
        if self._pulse >= 255:
            self._pulse_dir = -1
        elif self._pulse <= 80:
            self._pulse_dir = 1
        self.update()

    # ------------------------------------------------------------------
    def paintEvent(self, event):
        super().paintEvent(event)
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)

        w, h = self.width(), self.height()
        cx, cy = w / 2, h / 2

        if self._running:
            # ── Running state: animated scan lines ──────────────────────
            # Dark overlay
            painter.fillRect(0, 0, w, h, QColor("#0D1B2A"))

            # Horizontal scan line
            scan_y = int((self._pulse / 255) * h)
            pen = QPen(QColor(45, 125, 210, 60))
            pen.setWidth(2)
            painter.setPen(pen)
            painter.drawLine(0, scan_y, w, scan_y)

            # Grid overlay
            pen.setColor(QColor(45, 125, 210, 15))
            pen.setWidth(1)
            painter.setPen(pen)
            step = 30
            for x in range(0, w, step):
                painter.drawLine(x, 0, x, h)
            for y in range(0, h, step):
                painter.drawLine(0, y, w, y)

            # Corner brackets
            pen.setColor(QColor("#2D7DD2"))
            pen.setWidth(2)
            painter.setPen(pen)
            brk = 20
            off = 16
            for bx, by in [(off, off), (w - off, off), (off, h - off), (w - off, h - off)]:
                sx = 1 if bx == off else -1
                sy = 1 if by == off else -1
                painter.drawLine(bx, by, bx + sx * brk, by)
                painter.drawLine(bx, by, bx, by + sy * brk)

            # "LIVE" indicator
            live_alpha = self._pulse
            painter.setBrush(QColor(231, 76, 60, live_alpha))
            painter.setPen(Qt.NoPen)
            painter.drawEllipse(w - 52, 16, 10, 10)

            painter.setPen(QColor(255, 255, 255, 200))
            f = QFont("Segoe UI", 10, QFont.Bold)
            painter.setFont(f)
            painter.drawText(w - 38, 26, "LIVE")

        else:
            # ── Idle state: camera icon + instruction text ───────────────
            painter.fillRect(0, 0, w, h, QColor("#111827"))

            # Camera body
            body_color = QColor(50, 80, 120)
            painter.setBrush(QBrush(body_color))
            painter.setPen(Qt.NoPen)
            bw, bh = 90, 60
            painter.drawRoundedRect(int(cx - bw / 2), int(cy - bh / 2), bw, bh, 10, 10)

            # Lens outer
            painter.setBrush(QColor(30, 50, 80))
            painter.drawEllipse(int(cx - 22), int(cy - 22), 44, 44)

            # Lens inner
            painter.setBrush(QColor(20, 35, 60))
            painter.drawEllipse(int(cx - 14), int(cy - 14), 28, 28)

            # Lens shimmer
            painter.setBrush(QColor(80, 130, 200, 120))
            painter.drawEllipse(int(cx - 7), int(cy - 10), 8, 8)

            # Viewfinder bump
            painter.setBrush(body_color)
            painter.drawRoundedRect(int(cx - 15), int(cy - bh / 2 - 12), 30, 14, 5, 5)

            # Text
            painter.setPen(QColor(100, 140, 180))
            f = QFont("Segoe UI", 11)
            painter.setFont(f)
            painter.drawText(
                0, int(cy + 54), w, 30, Qt.AlignCenter, "Tekan  START  untuk memulai kamera"
            )

            painter.setPen(QColor(50, 80, 120))
            f2 = QFont("Segoe UI", 9)
            painter.setFont(f2)
            painter.drawText(
                0, int(cy + 76), w, 24, Qt.AlignCenter, "Camera feed placeholder"
            )

        painter.end()
