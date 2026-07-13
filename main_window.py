"""
main_window.py
QMainWindow shell — sidebar dihapus, hanya QStackedWidget penuh.

Revisi responsivitas:
- Minimum size diturunkan (900x640 -> 680x560) supaya breakpoint di
  MonitoringPage & RespondentDialog benar-benar bisa kepakai saat window
  di-resize kecil / di-snap ke setengah layar.
"""

from __future__ import annotations

from PySide6.QtWidgets import (
    QMainWindow,
    QWidget,
    QHBoxLayout,
    QVBoxLayout,
    QStackedWidget,
)
from PySide6.QtCore import Qt

from pages.main_page import MainPage
from pages.monitoring_page import MonitoringPage

# Page index constants
PAGE_MAIN = 0
PAGE_MONITORING = 1


class MainWindow(QMainWindow):
    """
    Application shell.
    Tidak ada sidebar — QStackedWidget mengisi seluruh window.
    Navigasi dilakukan via signal dari masing-masing page.
    """

    def __init__(self):
        super().__init__()
        self.setWindowTitle("Bionic Foot — Sistem Pengukuran Sudut Ankle")

        # Batas minimum diturunkan dari (900, 640) -> (680, 560) supaya
        # window masih bisa di-resize wajar (misal di-snap ke setengah
        # layar) tanpa konten kepotong, dan breakpoint responsif di
        # MonitoringPage/RespondentDialog benar-benar aktif kepakai.
        self.setMinimumSize(680, 560)
        self.resize(1200, 760)

        central = QWidget()
        self.setCentralWidget(central)

        self._root_layout = QHBoxLayout(central)
        self._root_layout.setContentsMargins(0, 0, 0, 0)
        self._root_layout.setSpacing(0)

        self._build_content_area()
        self._connect_signals()

        # Start on main page
        self._set_page(PAGE_MAIN)

    # ── Content Stack ─────────────────────────────────────────────────────────
    def _build_content_area(self):
        self.stack = QStackedWidget()
        self.stack.setObjectName("AppRoot")

        self.main_page = MainPage()
        self.monitoring_page = MonitoringPage()

        self.stack.addWidget(self.main_page)        # index 0
        self.stack.addWidget(self.monitoring_page)  # index 1

        self._root_layout.addWidget(self.stack)

    # ── Signals ───────────────────────────────────────────────────────────────
    def _connect_signals(self):
        self.main_page.navigate_to_monitoring.connect(self._go_to_monitoring)
        self.monitoring_page.navigate_back.connect(self._go_to_main)

    # ── Navigation helpers ────────────────────────────────────────────────────
    def _set_page(self, index: int):
        self.stack.setCurrentIndex(index)

    def _go_to_monitoring(self, respondent: dict):
        self.monitoring_page.set_respondent(respondent)
        self._set_page(PAGE_MONITORING)

    def _go_to_main(self):
        self._set_page(PAGE_MAIN)