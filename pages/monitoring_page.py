"""
pages/monitoring_page.py
Monitoring page — live camera placeholder, control buttons, metric cards,
respondent info header.
"""

from __future__ import annotations

from PySide6.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QFrame,
    QDoubleSpinBox,
    QSizePolicy,
    QScrollArea,
    QGridLayout,
    QSpacerItem,
)
from PySide6.QtCore import Qt, Signal, QTimer
from PySide6.QtGui import QFont

from app_camera import AnkleCameraWidget
from widgets.metric_card import MetricCard
from widgets.status_badge import StatusBadge


class MonitoringPage(QWidget):
    """
    Halaman monitoring pengukuran sudut ankle untuk satu responden.

    Signals:
        navigate_back: Emitted when user clicks "Kembali".
    """

    navigate_back = Signal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self._respondent: dict = {}
        self._is_running = False
        self._elapsed_seconds = 0
        self._timer = QTimer(self)
        self._timer.timeout.connect(self._tick_timer)
        self._build_ui()

    # ── UI Construction ─────────────────────────────────────────────────────
    def _build_ui(self):
        scroll = QScrollArea(self)
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.NoFrame)

        container = QWidget()
        container.setObjectName("AppRoot")
        root = QVBoxLayout(container)
        root.setContentsMargins(32, 24, 32, 28)
        root.setSpacing(0)
        scroll.setWidget(container)

        # Outer layout (full page)
        page_layout = QVBoxLayout(self)
        page_layout.setContentsMargins(0, 0, 0, 0)
        page_layout.addWidget(scroll)

        # ── Back + Breadcrumb ─────────────────────────────────────────────
        nav_row = QHBoxLayout()
        back_btn = QPushButton("←  Kembali ke Daftar Responden")
        back_btn.setObjectName("BackBtn")
        back_btn.setCursor(Qt.PointingHandCursor)
        back_btn.clicked.connect(self._on_back_clicked)
        nav_row.addWidget(back_btn)
        nav_row.addStretch()
        root.addLayout(nav_row)
        root.addSpacing(8)

        # ── Page Title ────────────────────────────────────────────────────
        page_title_row = QHBoxLayout()
        page_title_lbl = QLabel("Monitoring Pengukuran")
        page_title_lbl.setObjectName("PageTitle")
        page_title_row.addWidget(page_title_lbl)
        page_title_row.addStretch()
        root.addLayout(page_title_row)
        root.addSpacing(20)

        # ── Respondent Info Card ──────────────────────────────────────────
        info_card = QFrame()
        info_card.setObjectName("Card")
        info_layout = QHBoxLayout(info_card)
        info_layout.setContentsMargins(24, 18, 24, 18)
        info_layout.setSpacing(0)

        # Avatar circle (drawn via stylesheet)
        self.avatar_lbl = QLabel("B")
        self.avatar_lbl.setFixedSize(52, 52)
        self.avatar_lbl.setAlignment(Qt.AlignCenter)
        self.avatar_lbl.setStyleSheet(
            "background-color: #2D7DD2; color: #FFFFFF; border-radius: 26px;"
            " font-size: 20px; font-weight: 700;"
        )
        info_layout.addWidget(self.avatar_lbl)
        info_layout.addSpacing(20)

        # Respondent details
        details_col = QVBoxLayout()
        details_col.setSpacing(4)
        self.respondent_name = QLabel("—")
        self.respondent_name.setStyleSheet(
            "font-size: 18px; font-weight: 700; color: #1A2340; background: transparent;"
        )
        self.respondent_meta = QLabel("—")
        self.respondent_meta.setStyleSheet(
            "font-size: 13px; color: #6B7A99; background: transparent;"
        )
        details_col.addWidget(self.respondent_name)
        details_col.addWidget(self.respondent_meta)
        info_layout.addLayout(details_col)
        info_layout.addStretch()

        # Status badge
        status_col = QVBoxLayout()
        status_col.setAlignment(Qt.AlignCenter)
        status_label = QLabel("STATUS")
        status_label.setObjectName("SectionLabel")
        self.status_badge = StatusBadge("Normal", large=True)
        status_col.addWidget(status_label, alignment=Qt.AlignCenter)
        status_col.addSpacing(4)
        status_col.addWidget(self.status_badge, alignment=Qt.AlignCenter)
        info_layout.addLayout(status_col)
        info_layout.addSpacing(32)

        # Session ID / timestamp info
        session_col = QVBoxLayout()
        session_col.setAlignment(Qt.AlignCenter)
        session_label_title = QLabel("SESI")
        session_label_title.setObjectName("SectionLabel")
        self.session_label = QLabel("#001")
        self.session_label.setStyleSheet(
            "font-size: 20px; font-weight: 800; color: #2D7DD2; background: transparent;"
        )
        session_col.addWidget(session_label_title, alignment=Qt.AlignCenter)
        session_col.addSpacing(4)
        session_col.addWidget(self.session_label, alignment=Qt.AlignCenter)
        info_layout.addLayout(session_col)

        root.addWidget(info_card)
        root.addSpacing(20)

        # ── Main 2-column layout ──────────────────────────────────────────
        main_cols = QHBoxLayout()
        main_cols.setSpacing(20)

        # ── LEFT: Camera + Controls ───────────────────────────────────────
        left_col = QVBoxLayout()
        left_col.setSpacing(16)

        # Camera
        cam_header = QLabel("Live Camera Feed")
        cam_header.setStyleSheet(
            "font-size: 13px; font-weight: 700; color: #6B7A99; background: transparent;"
        )
        left_col.addWidget(cam_header)

        self.camera = AnkleCameraWidget(camera_source=1, embedded=True)
        self.camera.setMinimumSize(460, 320)
        self.camera.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        self.camera.angle_updated.connect(self._on_angle_updated)
        left_col.addWidget(self.camera, stretch=1)

        # ── Control Buttons ───────────────────────────────────────────────
        ctrl_card = QFrame()
        ctrl_card.setObjectName("Card")
        ctrl_layout = QVBoxLayout(ctrl_card)
        ctrl_layout.setContentsMargins(20, 16, 20, 16)
        ctrl_layout.setSpacing(12)

        ctrl_title = QLabel("KONTROL SESI")
        ctrl_title.setObjectName("SectionLabel")
        ctrl_layout.addWidget(ctrl_title)

        btn_row = QHBoxLayout()
        btn_row.setSpacing(10)

        self.start_btn = QPushButton("▶  Start")
        self.start_btn.setObjectName("SuccessBtn")
        self.start_btn.setFixedHeight(44)
        self.start_btn.setCursor(Qt.PointingHandCursor)
        self.start_btn.clicked.connect(self._on_start)

        self.stop_btn = QPushButton("⏹  Stop")
        self.stop_btn.setObjectName("DangerBtn")
        self.stop_btn.setFixedHeight(44)
        self.stop_btn.setCursor(Qt.PointingHandCursor)
        self.stop_btn.setEnabled(False)
        self.stop_btn.clicked.connect(self._on_stop)

        self.submit_btn = QPushButton("✔  Submit")
        self.submit_btn.setObjectName("PrimaryBtn")
        self.submit_btn.setFixedHeight(44)
        self.submit_btn.setCursor(Qt.PointingHandCursor)
        self.submit_btn.setEnabled(False)
        self.submit_btn.clicked.connect(self._on_submit)

        self.export_btn = QPushButton("⬇  Export")
        self.export_btn.setObjectName("GhostBtn")
        self.export_btn.setFixedHeight(44)
        self.export_btn.setCursor(Qt.PointingHandCursor)
        self.export_btn.setEnabled(False)

        btn_row.addWidget(self.start_btn)
        btn_row.addWidget(self.stop_btn)
        btn_row.addWidget(self.submit_btn)
        btn_row.addWidget(self.export_btn)
        ctrl_layout.addLayout(btn_row)

        # Status indicator strip
        self.status_strip = QLabel("● Sesi belum dimulai")
        self.status_strip.setStyleSheet(
            "font-size: 12px; color: #9AA3B8; background: transparent; padding-top: 4px;"
        )
        ctrl_layout.addWidget(self.status_strip)
        left_col.addWidget(ctrl_card)

        main_cols.addLayout(left_col, stretch=3)

        # ── RIGHT: Metrics + Input ─────────────────────────────────────────
        right_col = QVBoxLayout()
        right_col.setSpacing(14)

        metrics_title = QLabel("Data Pengukuran")
        metrics_title.setStyleSheet(
            "font-size: 13px; font-weight: 700; color: #6B7A99; background: transparent;"
        )
        right_col.addWidget(metrics_title)

        # Sudut Ankle card (primary)
        self.card_sudut = MetricCard(
            label="Sudut Ankle",
            value="23.4",
            unit="°",
            accent_color="#2D7DD2",
        )
        right_col.addWidget(self.card_sudut)

        # Waktu Tempuh card
        self.card_waktu = MetricCard(
            label="Waktu Tempuh",
            value="00:00",
            unit="s",
            accent_color="#8E44AD",
        )
        right_col.addWidget(self.card_waktu)

        # ── Jarak input card ───────────────────────────────────────────────
        jarak_card = QFrame()
        jarak_card.setObjectName("Card")
        jarak_layout = QVBoxLayout(jarak_card)
        jarak_layout.setContentsMargins(20, 16, 20, 16)
        jarak_layout.setSpacing(10)

        jarak_title = QLabel("JARAK TEMPUH")
        jarak_title.setObjectName("SectionLabel")
        jarak_layout.addWidget(jarak_title)

        jarak_input_row = QHBoxLayout()
        jarak_input_row.setSpacing(10)
        self.jarak_input = QDoubleSpinBox()
        self.jarak_input.setRange(0.0, 999.9)
        self.jarak_input.setSingleStep(0.1)
        self.jarak_input.setValue(6.0)
        self.jarak_input.setDecimals(1)
        self.jarak_input.setSuffix("  m")
        self.jarak_input.setFixedHeight(44)
        self.jarak_input.setStyleSheet(
            "font-size: 18px; font-weight: 700; color: #1A7A45;"
        )

        jarak_input_row.addWidget(self.jarak_input, stretch=1)
        jarak_layout.addLayout(jarak_input_row)

        jarak_hint = QLabel("Input manual jarak lintasan pengujian")
        jarak_hint.setStyleSheet("font-size: 11px; color: #B0BADA; background: transparent;")
        jarak_layout.addWidget(jarak_hint)
        right_col.addWidget(jarak_card)

        # ── Gait Info mini cards ───────────────────────────────────────────
        gait_card = QFrame()
        gait_card.setObjectName("Card")
        gait_layout = QVBoxLayout(gait_card)
        gait_layout.setContentsMargins(20, 16, 20, 16)
        gait_layout.setSpacing(12)

        gait_title_row = QHBoxLayout()
        gait_title = QLabel("INFO GAIT")
        gait_title.setObjectName("SectionLabel")
        gait_title_row.addWidget(gait_title)
        gait_layout.addLayout(gait_title_row)

        grid = QGridLayout()
        grid.setSpacing(10)
        gait_items = [
            ("Kadence", "—", "steps/min"),
            ("Kecepatan", "—", "m/s"),
            ("Langkah", "—", "steps"),
            ("Fleksi Maks", "—", "°"),
        ]
        for i, (lbl, val, unit) in enumerate(gait_items):
            mini = self._make_mini_stat(lbl, val, unit)
            grid.addWidget(mini, i // 2, i % 2)
        gait_layout.addLayout(grid)
        right_col.addWidget(gait_card)

        right_col.addStretch()
        main_cols.addLayout(right_col, stretch=2)

        root.addLayout(main_cols, stretch=1)

    # ── Mini Stat Helper ─────────────────────────────────────────────────────
    def _make_mini_stat(self, label: str, value: str, unit: str) -> QFrame:
        f = QFrame()
        f.setStyleSheet(
            "QFrame { background-color: #F7F9FD; border: 1px solid #E8EDF5;"
            " border-radius: 10px; }"
        )
        layout = QVBoxLayout(f)
        layout.setContentsMargins(12, 10, 12, 10)
        layout.setSpacing(2)

        lbl = QLabel(label.upper())
        lbl.setStyleSheet("font-size: 10px; font-weight: 700; color: #9AA3B8; background: transparent; letter-spacing: 0.5px;")

        val_row = QHBoxLayout()
        val_row.setSpacing(4)
        v = QLabel(value)
        v.setStyleSheet("font-size: 20px; font-weight: 800; color: #1A2340; background: transparent;")
        u = QLabel(unit)
        u.setStyleSheet("font-size: 11px; color: #9AA3B8; background: transparent; padding-top: 6px;")
        val_row.addWidget(v)
        val_row.addWidget(u)
        val_row.addStretch()

        layout.addWidget(lbl)
        layout.addLayout(val_row)
        return f

    # ── Public API ───────────────────────────────────────────────────────────
    def set_respondent(self, data: dict):
        """Load a respondent into this page."""
        self._respondent = data
        name = data.get("nama", "—")
        umur = data.get("umur", "—")
        jk = data.get("jenis_kelamin", "—")
        status = data.get("status", "Normal")

        initial = name[0].upper() if name else "?"
        self.avatar_lbl.setText(initial)

        is_normal = status == "Normal"
        avatar_color = "#2D7DD2" if is_normal else "#E74C3C"
        self.avatar_lbl.setStyleSheet(
            f"background-color: {avatar_color}; color: #FFFFFF; border-radius: 26px;"
            " font-size: 20px; font-weight: 700;"
        )

        self.respondent_name.setText(name)
        self.respondent_meta.setText(f"{umur} tahun  •  {jk}")
        self.status_badge.set_status(status)

        # Reset state
        self._reset_session()

    # ── Session Control ───────────────────────────────────────────────────────
    def _on_start(self):
        self._is_running = True
        self._elapsed_seconds = 0
        self._timer.start(1000)
        self.camera.start_camera()
        self.start_btn.setEnabled(False)
        self.stop_btn.setEnabled(True)
        self.submit_btn.setEnabled(False)
        self.export_btn.setEnabled(False)
        self.status_strip.setText("🔴  Sesi berjalan — merekam data pengukuran...")
        self.status_strip.setStyleSheet(
            "font-size: 12px; color: #E74C3C; background: transparent; padding-top: 4px;"
        )
        # Sudut ankle sekarang di-update secara real-time lewat sinyal
        # angle_updated dari AnkleCameraWidget (lihat _on_angle_updated).
        self.card_sudut.set_value("—")

    def _on_stop(self):
        self._is_running = False
        self._timer.stop()
        self.camera.stop_camera()
        self.start_btn.setEnabled(True)
        self.stop_btn.setEnabled(False)
        self.submit_btn.setEnabled(True)
        self.export_btn.setEnabled(True)
        self.status_strip.setText("✅  Sesi dihentikan. Data siap untuk di-submit.")
        self.status_strip.setStyleSheet(
            "font-size: 12px; color: #27AE60; background: transparent; padding-top: 4px;"
        )

    def _on_submit(self):
        self.submit_btn.setEnabled(False)
        self.status_strip.setText("📤  Data berhasil disubmit. Siap untuk sesi baru.")
        self.status_strip.setStyleSheet(
            "font-size: 12px; color: #2D7DD2; background: transparent; padding-top: 4px;"
        )
        self.start_btn.setEnabled(True)

    def _reset_session(self):
        self._is_running = False
        self._elapsed_seconds = 0
        self._timer.stop()
        self.camera.stop_camera()
        self.start_btn.setEnabled(True)
        self.stop_btn.setEnabled(False)
        self.submit_btn.setEnabled(False)
        self.export_btn.setEnabled(False)
        self.card_sudut.set_value("—")
        self.card_waktu.set_value("00:00")
        self.status_strip.setText("● Sesi belum dimulai")
        self.status_strip.setStyleSheet(
            "font-size: 12px; color: #9AA3B8; background: transparent; padding-top: 4px;"
        )

    def _tick_timer(self):
        self._elapsed_seconds += 1
        minutes = self._elapsed_seconds // 60
        seconds = self._elapsed_seconds % 60
        self.card_waktu.set_value(f"{minutes:02d}:{seconds:02d}")

    # ── Camera integration ──────────────────────────────────────────────────
    def _on_angle_updated(self, angle, side_label):
        """Called every frame via AnkleCameraWidget.angle_updated.
        Pushes the live ankle angle from pose_tracker.py into the metric card."""
        if angle is None:
            self.card_sudut.set_value("—")
        else:
            self.card_sudut.set_value(f"{angle:.1f}")

    def _on_back_clicked(self):
        """Make sure the camera thread is stopped before leaving this page,
        since AnkleCameraWidget is a plain QWidget and won't get its own
        closeEvent when this page is swapped out (e.g. in a QStackedWidget)."""
        self.camera.stop_camera()
        self.navigate_back.emit()

    def stop_camera(self):
        """Public passthrough so the host app (main window) can stop the
        camera when the whole application is closing, e.g.:

            def closeEvent(self, event):
                self.monitoring_page.stop_camera()
                super().closeEvent(event)
        """
        self.camera.stop_camera()