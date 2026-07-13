"""
pages/monitoring_page.py

"""

from __future__ import annotations

from PySide6.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QGridLayout,
    QLabel,
    QPushButton,
    QFrame,
    QDoubleSpinBox,
    QSizePolicy,
    QScrollArea,
)
from PySide6.QtCore import Qt, Signal, QTimer

from widgets.camera_placeholder import CameraPlaceholder
from widgets.metric_card import MetricCard
from widgets.status_badge import StatusBadge


class MonitoringPage(QWidget):
    """
    Halaman monitoring pengukuran sudut ankle untuk satu responden.

    Signals:
        navigate_back: Emitted when user clicks "Kembali".
    """

    navigate_back = Signal()

    # ── Breakpoint (px) ──────────────────────────────────────────────────────
    METRICS_BREAKPOINT = 820   # di bawah ini, card metrik ditumpuk 1 kolom
    HEADER_BREAKPOINT = 760    # di bawah ini, tombol pindah ke baris sendiri

    def __init__(self, parent=None):
        super().__init__(parent)
        self._respondent: dict = {}
        self._is_running = False
        self._elapsed_seconds = 0
        self._timer = QTimer(self)
        self._timer.timeout.connect(self._tick_timer)

        # State breakpoint — dipakai resizeEvent supaya nggak rebuild
        # layout terus-menerus di setiap event resize kalau lebar belum
        # melewati ambang batas.
        self._metrics_columns = 3
        self._header_is_wide = True

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
        back_btn.clicked.connect(self.navigate_back.emit)
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

        self.avatar_lbl = QLabel("B")
        self.avatar_lbl.setFixedSize(52, 52)
        self.avatar_lbl.setAlignment(Qt.AlignCenter)
        self.avatar_lbl.setStyleSheet(
            "background-color: #3E6E63; color: #FFFFFF; border-radius: 26px;"
            " font-size: 20px; font-weight: 700;"
        )
        info_layout.addWidget(self.avatar_lbl)
        info_layout.addSpacing(20)

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

        session_col = QVBoxLayout()
        session_col.setAlignment(Qt.AlignCenter)
        session_label_title = QLabel("SESI")
        session_label_title.setObjectName("SectionLabel")
        self.session_label = QLabel("#001")
        self.session_label.setStyleSheet(
            "font-size: 20px; font-weight: 800; color: #3E6E63; background: transparent;"
        )
        session_col.addWidget(session_label_title, alignment=Qt.AlignCenter)
        session_col.addSpacing(4)
        session_col.addWidget(self.session_label, alignment=Qt.AlignCenter)
        info_layout.addLayout(session_col)

        root.addWidget(info_card)
        root.addSpacing(20)

        # ── Card Metrik (grid responsif: 3 kolom -> 1 kolom) ───────────────
        self.card_sudut = MetricCard(
            label="Sudut Ankle",
            value="—",
            unit="°",
        )
        self.card_waktu = MetricCard(
            label="Waktu Tempuh",
            value="00:00",
            unit="s",
        )

        # Jarak: tetap sebagai card input manual (QDoubleSpinBox), tapi
        # ditata bersama card metrik lain dalam grid yang sama.
        jarak_card = QFrame()
        jarak_card.setObjectName("Card")
        jarak_layout = QVBoxLayout(jarak_card)
        jarak_layout.setContentsMargins(20, 16, 20, 16)
        jarak_layout.setSpacing(6)

        jarak_title = QLabel("JARAK TEMPUH")
        jarak_title.setObjectName("SectionLabel")
        jarak_layout.addWidget(jarak_title)

        jarak_input_row = QHBoxLayout()
        jarak_input_row.setSpacing(6)
        self.jarak_input = QDoubleSpinBox()
        self.jarak_input.setRange(0.0, 999.9)
        self.jarak_input.setSingleStep(0.1)
        self.jarak_input.setValue(0.0)
        self.jarak_input.setDecimals(1)
        self.jarak_input.setSuffix("  m")
        self.jarak_input.setFixedHeight(38)
        self.jarak_input.setStyleSheet(
            "font-size: 15px; font-weight: 700; color: #1A2340;"
        )
        jarak_input_row.addWidget(self.jarak_input, stretch=1)
        jarak_layout.addLayout(jarak_input_row)

        self._metric_widgets = [self.card_sudut, self.card_waktu, jarak_card]

        self.metrics_grid = QGridLayout()
        self.metrics_grid.setSpacing(16)
        self._layout_metrics_grid(3)

        root.addLayout(self.metrics_grid)
        root.addSpacing(20)

        # ── Judul "Live Camera Feed" + Tombol Kontrol (container responsif) ─
        self.cam_header_label = QLabel("Live Camera Feed")
        self.cam_header_label.setStyleSheet(
            "font-size: 13px; font-weight: 700; color: #6B7A99; background: transparent;"
        )

        self.start_btn = QPushButton("▶  Start")
        self.start_btn.setObjectName("SuccessBtn")
        self.start_btn.setFixedHeight(40)
        self.start_btn.setCursor(Qt.PointingHandCursor)
        self.start_btn.clicked.connect(self._on_start)

        self.stop_btn = QPushButton("⏹  Stop")
        self.stop_btn.setObjectName("DangerBtn")
        self.stop_btn.setFixedHeight(40)
        self.stop_btn.setCursor(Qt.PointingHandCursor)
        self.stop_btn.setEnabled(False)
        self.stop_btn.clicked.connect(self._on_stop)

        self.submit_btn = QPushButton("✔  Submit")
        self.submit_btn.setObjectName("PrimaryBtn")
        self.submit_btn.setFixedHeight(40)
        self.submit_btn.setCursor(Qt.PointingHandCursor)
        self.submit_btn.setEnabled(False)
        self.submit_btn.clicked.connect(self._on_submit)

        self.export_btn = QPushButton("⬇  Export")
        self.export_btn.setObjectName("GhostBtn")
        self.export_btn.setFixedHeight(40)
        self.export_btn.setCursor(Qt.PointingHandCursor)
        self.export_btn.setEnabled(False)

        self._cam_buttons = [self.start_btn, self.stop_btn, self.submit_btn, self.export_btn]

        self.cam_header_container = QWidget()
        self._build_cam_header(wide=True)

        root.addWidget(self.cam_header_container)
        root.addSpacing(8)

        # Status strip (di bawah baris judul+tombol, di atas kamera)
        self.status_strip = QLabel("● Sesi belum dimulai")
        self.status_strip.setStyleSheet(
            "font-size: 11px; color: #9AA3B8; background: transparent;"
        )
        root.addWidget(self.status_strip)
        root.addSpacing(10)

        # ── Kamera Full-Width ───────────────────────────────────────────────
        self.camera = CameraPlaceholder()
        self.camera.setMinimumSize(400, 380)
        self.camera.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        root.addWidget(self.camera, stretch=1)

    # ── Responsive layout helpers ────────────────────────────────────────────
    def _layout_metrics_grid(self, columns: int):
        """Susun ulang card metrik ke grid dengan jumlah kolom tertentu."""
        for w in self._metric_widgets:
            self.metrics_grid.removeWidget(w)
        for i, w in enumerate(self._metric_widgets):
            row, col = divmod(i, columns)
            self.metrics_grid.addWidget(w, row, col)
        for col in range(columns):
            self.metrics_grid.setColumnStretch(col, 1)
        self._metrics_columns = columns

    def _build_cam_header(self, wide: bool):
        """Bangun ulang baris judul+tombol: sejajar (wide) atau ditumpuk (narrow)."""
        old_layout = self.cam_header_container.layout()
        if old_layout is not None:
            while old_layout.count():
                item = old_layout.takeAt(0)
                w = item.widget()
                if w is not None:
                    w.setParent(self.cam_header_container)
                sub_layout = item.layout()
                if sub_layout is not None:
                    # btn_row (QHBoxLayout bersarang di mode narrow) juga
                    # perlu dikosongkan dulu sebelum dibuang, dengan alasan
                    # yang sama seperti di atas.
                    while sub_layout.count():
                        sub_item = sub_layout.takeAt(0)
                        sub_w = sub_item.widget()
                        if sub_w is not None:
                            sub_w.setParent(self.cam_header_container)

            # Sekarang old_layout sudah kosong (tidak ada widget di
            # dalamnya), jadi aman untuk dibuang lewat idiom standar ini.
            QWidget().setLayout(old_layout)

        if wide:
            layout = QHBoxLayout()
            layout.setContentsMargins(0, 0, 0, 0)
            layout.addWidget(self.cam_header_label)
            layout.addStretch()
            for btn in self._cam_buttons:
                layout.addWidget(btn)
        else:
            layout = QVBoxLayout()
            layout.setContentsMargins(0, 0, 0, 0)
            layout.setSpacing(10)
            layout.addWidget(self.cam_header_label)
            btn_row = QHBoxLayout()
            btn_row.setSpacing(8)
            for btn in self._cam_buttons:
                btn_row.addWidget(btn)
            layout.addLayout(btn_row)

        self.cam_header_container.setLayout(layout)
        self._header_is_wide = wide

    def resizeEvent(self, event):
        super().resizeEvent(event)
        w = event.size().width()

        columns = 1 if w < self.METRICS_BREAKPOINT else 3
        if columns != self._metrics_columns:
            self._layout_metrics_grid(columns)

        wide = w >= self.HEADER_BREAKPOINT
        if wide != self._header_is_wide:
            self._build_cam_header(wide)

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
        avatar_color = "#3E6E63" if is_normal else "#C0503F"
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
        self.camera.set_running(True)
        self.start_btn.setEnabled(False)
        self.stop_btn.setEnabled(True)
        self.submit_btn.setEnabled(False)
        self.export_btn.setEnabled(False)
        self.status_strip.setText("🔴 Sesi berjalan...")
        self.status_strip.setStyleSheet(
            "font-size: 11px; color: #C0503F; background: transparent;"
        )
        self.card_sudut.set_value("23.4")

    def _on_stop(self):
        self._is_running = False
        self._timer.stop()
        self.camera.set_running(False)
        self.start_btn.setEnabled(True)
        self.stop_btn.setEnabled(False)
        self.submit_btn.setEnabled(True)
        self.export_btn.setEnabled(True)
        self.status_strip.setText("✅ Sesi dihentikan. Siap di-submit.")
        self.status_strip.setStyleSheet(
            "font-size: 11px; color: #4C8F5E; background: transparent;"
        )

    def _on_submit(self):
        self.submit_btn.setEnabled(False)
        self.status_strip.setText("📤 Data disubmit. Siap sesi baru.")
        self.status_strip.setStyleSheet(
            "font-size: 11px; color: #3E6E63; background: transparent;"
        )
        self.start_btn.setEnabled(True)

    def _reset_session(self):
        self._is_running = False
        self._elapsed_seconds = 0
        self._timer.stop()
        self.camera.set_running(False)
        self.start_btn.setEnabled(True)
        self.stop_btn.setEnabled(False)
        self.submit_btn.setEnabled(False)
        self.export_btn.setEnabled(False)
        self.card_sudut.set_value("—")
        self.card_waktu.set_value("00:00")
        self.status_strip.setText("● Sesi belum dimulai")
        self.status_strip.setStyleSheet(
            "font-size: 11px; color: #9AA3B8; background: transparent;"
        )

    def _tick_timer(self):
        self._elapsed_seconds += 1
        minutes = self._elapsed_seconds // 60
        seconds = self._elapsed_seconds % 60
        self.card_waktu.set_value(f"{minutes:02d}:{seconds:02d}")
        import random
        base = 23.4
        variation = random.uniform(-2.5, 2.5)
        self.card_sudut.set_value(f"{base + variation:.1f}")