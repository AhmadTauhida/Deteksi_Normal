"""
pages/main_page.py
Main page — Daftar Responden dengan search, filter, tabel, dan tombol tambah.
Revisi: sidebar dihapus, kolom tabel proporsional, teks tidak terpotong.
"""

from __future__ import annotations

from PySide6.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QTableWidget,
    QTableWidgetItem,
    QHeaderView,
    QFrame,
    QLineEdit,
    QComboBox,
    QAbstractItemView,
)
from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QFont

from widgets.status_badge import StatusBadge
from widgets.respondent_dialog import RespondentDialog

# ── Dummy initial data ──────────────────────────────────────────────────────
DUMMY_RESPONDENTS: list[dict] = [
    {"nama": "Budi Santoso",    "umur": 45, "jenis_kelamin": "Laki-laki",  "status": "Normal"},
    {"nama": "Siti Rahayu",     "umur": 38, "jenis_kelamin": "Perempuan",  "status": "Tidak Normal"},
    {"nama": "Ahmad Fauzi",     "umur": 52, "jenis_kelamin": "Laki-laki",  "status": "Normal"},
    {"nama": "Dewi Lestari",    "umur": 60, "jenis_kelamin": "Perempuan",  "status": "Tidak Normal"},
    {"nama": "Hendra Wijaya",   "umur": 33, "jenis_kelamin": "Laki-laki",  "status": "Normal"},
    {"nama": "Rina Kusumawati", "umur": 41, "jenis_kelamin": "Perempuan",  "status": "Normal"},
    {"nama": "Joko Susilo",     "umur": 57, "jenis_kelamin": "Laki-laki",  "status": "Tidak Normal"},
]

COL_NAMA, COL_UMUR, COL_JK, COL_STATUS, COL_AKSI = 0, 1, 2, 3, 4

# Lebar tetap kolom non-stretch (px) — cukup untuk konten terpanjang
COL_UMUR_W   = 90    # "60 thn" → cukup 90
COL_JK_W     = 160   # "♀  Perempuan" → 160
COL_STATUS_W = 150   # "Tidak Normal" badge → 150
COL_AKSI_W   = 150   # "▶  Monitoring" button → 150


class MainPage(QWidget):
    """
    Halaman utama berisi daftar responden.

    Signals:
        navigate_to_monitoring (dict): Emitted when user clicks Monitoring button.
    """

    navigate_to_monitoring = Signal(dict)

    def __init__(self, parent=None):
        super().__init__(parent)
        self._all_data: list[dict] = list(DUMMY_RESPONDENTS)
        self._build_ui()
        self._populate_table(self._all_data)

    # ── UI Construction ─────────────────────────────────────────────────────
    def _build_ui(self):
        root = QVBoxLayout(self)
        root.setContentsMargins(40, 32, 40, 28)
        root.setSpacing(0)

        # ── Top Header ────────────────────────────────────────────────────
        header_row = QHBoxLayout()
        header_row.setSpacing(0)

        left_col = QVBoxLayout()
        left_col.setSpacing(5)

        breadcrumb = QLabel("🦶  Bionic Foot  /  Daftar Responden")
        breadcrumb.setStyleSheet(
            "font-size: 12px; color: #9AA3B8; background: transparent; font-weight: 500;"
        )
        title = QLabel("Daftar Responden")
        title.setObjectName("PageTitle")
        subtitle = QLabel("Kelola dan pantau data responden pengukuran sudut ankle.")
        subtitle.setObjectName("PageSubtitle")

        left_col.addWidget(breadcrumb)
        left_col.addWidget(title)
        left_col.addWidget(subtitle)
        header_row.addLayout(left_col)
        header_row.addStretch()

        # Tambah Responden button — wide enough to show full text
        self.add_btn = QPushButton("＋  Tambah Responden")
        self.add_btn.setObjectName("PrimaryBtn")
        self.add_btn.setFixedHeight(44)
        self.add_btn.setMinimumWidth(180)
        self.add_btn.setCursor(Qt.PointingHandCursor)
        self.add_btn.clicked.connect(self._open_add_dialog)
        header_row.addWidget(self.add_btn)

        root.addLayout(header_row)
        root.addSpacing(28)

        # ── Toolbar: Search + Filter ──────────────────────────────────────
        toolbar = QHBoxLayout()
        toolbar.setSpacing(12)

        self.search_bar = QLineEdit()
        self.search_bar.setObjectName("SearchBar")
        self.search_bar.setPlaceholderText("🔍  Cari nama responden...")
        self.search_bar.setFixedHeight(42)
        self.search_bar.setMinimumWidth(300)
        self.search_bar.textChanged.connect(self._apply_filters)
        toolbar.addWidget(self.search_bar)

        filter_label = QLabel("Filter Status:")
        filter_label.setStyleSheet(
            "color: #6B7A99; font-size: 13px; background: transparent;"
        )
        self.filter_combo = QComboBox()
        self.filter_combo.setObjectName("FilterCombo")
        self.filter_combo.setFixedHeight(42)
        self.filter_combo.addItems(["Semua Status", "Normal", "Tidak Normal"])
        self.filter_combo.currentIndexChanged.connect(self._apply_filters)

        toolbar.addWidget(filter_label)
        toolbar.addWidget(self.filter_combo)
        toolbar.addStretch()

        self.count_label = QLabel()
        self.count_label.setStyleSheet(
            "color: #9AA3B8; font-size: 12px; background: transparent;"
        )
        toolbar.addWidget(self.count_label)

        root.addLayout(toolbar)
        root.addSpacing(16)

        # ── Table ─────────────────────────────────────────────────────────
        self.table = QTableWidget()
        self.table.setColumnCount(5)
        self.table.setHorizontalHeaderLabels(
            ["Nama Responden", "Umur", "Jenis Kelamin", "Status", "Aksi"]
        )

        hdr = self.table.horizontalHeader()
        hdr.setHighlightSections(False)

        # Kolom Nama: mengisi sisa ruang
        hdr.setSectionResizeMode(COL_NAMA, QHeaderView.Stretch)

        # Kolom lain: lebar tetap yang cukup
        for col, w in [
            (COL_UMUR,   COL_UMUR_W),
            (COL_JK,     COL_JK_W),
            (COL_STATUS, COL_STATUS_W),
            (COL_AKSI,   COL_AKSI_W),
        ]:
            hdr.setSectionResizeMode(col, QHeaderView.Fixed)
            self.table.setColumnWidth(col, w)

        self.table.verticalHeader().setVisible(False)
        self.table.setShowGrid(False)
        self.table.setAlternatingRowColors(True)
        self.table.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.table.setEditTriggers(QAbstractItemView.NoEditTriggers)
        self.table.setSelectionMode(QAbstractItemView.SingleSelection)
        self.table.setFocusPolicy(Qt.NoFocus)
        self.table.verticalHeader().setDefaultSectionSize(56)

        root.addWidget(self.table, stretch=1)

        # ── Summary Footer ────────────────────────────────────────────────
        root.addSpacing(12)
        footer = QHBoxLayout()
        self.total_label = QLabel()
        self.total_label.setStyleSheet(
            "color: #9AA3B8; font-size: 12px; background: transparent;"
        )
        footer.addWidget(self.total_label)
        footer.addStretch()
        root.addLayout(footer)

    # ── Data Handling ────────────────────────────────────────────────────────
    def _populate_table(self, data: list[dict]):
        self.table.setRowCount(0)
        for row_data in data:
            self._insert_row(row_data)

        n = len(data)
        self.count_label.setText(f"Menampilkan {n} responden")

        total   = len(self._all_data)
        normal  = sum(1 for d in self._all_data if d["status"] == "Normal")
        abnormal = total - normal
        self.total_label.setText(
            f"Total: {total}  •  Normal: {normal}  •  Tidak Normal: {abnormal}"
        )

    def _insert_row(self, data: dict):
        row = self.table.rowCount()
        self.table.insertRow(row)
        self.table.setRowHeight(row, 56)

        # ── Nama ─────────────────────────────────────────────────────────
        nama_item = QTableWidgetItem(data["nama"])
        nama_item.setFont(QFont("Segoe UI", 13, QFont.Medium))
        nama_item.setData(Qt.UserRole, data)
        nama_item.setToolTip(data["nama"])
        self.table.setItem(row, COL_NAMA, nama_item)

        # ── Umur ─────────────────────────────────────────────────────────
        umur_item = QTableWidgetItem(f"{data['umur']} thn")
        umur_item.setTextAlignment(Qt.AlignCenter)
        self.table.setItem(row, COL_UMUR, umur_item)

        # ── Jenis Kelamin ─────────────────────────────────────────────────
        jk_icon = "♂" if data["jenis_kelamin"] == "Laki-laki" else "♀"
        jk_item = QTableWidgetItem(f"{jk_icon}  {data['jenis_kelamin']}")
        jk_item.setTextAlignment(Qt.AlignCenter)
        self.table.setItem(row, COL_JK, jk_item)

        # ── Status badge ──────────────────────────────────────────────────
        badge = StatusBadge(data["status"])
        # Pastikan badge punya minimum width supaya teks tidak terpotong
        badge.setMinimumWidth(110)
        badge_container = QWidget()
        badge_container.setStyleSheet("background: transparent;")
        bc_layout = QHBoxLayout(badge_container)
        bc_layout.setContentsMargins(10, 8, 10, 8)
        bc_layout.addWidget(badge, alignment=Qt.AlignCenter)
        self.table.setCellWidget(row, COL_STATUS, badge_container)

        # ── Aksi: tombol Monitoring ───────────────────────────────────────
        monitor_btn = QPushButton("▶  Monitoring")
        monitor_btn.setObjectName("SecondaryBtn")
        monitor_btn.setCursor(Qt.PointingHandCursor)
        monitor_btn.setFixedHeight(36)
        # Pastikan teks tombol tidak terpotong
        monitor_btn.setMinimumWidth(120)
        monitor_btn.setStyleSheet(
            "QPushButton#SecondaryBtn { font-size: 12px; padding: 6px 14px; }"
        )

        btn_container = QWidget()
        btn_container.setStyleSheet("background: transparent;")
        btn_layout = QHBoxLayout(btn_container)
        btn_layout.setContentsMargins(8, 10, 8, 10)
        btn_layout.addWidget(monitor_btn)
        self.table.setCellWidget(row, COL_AKSI, btn_container)
        monitor_btn.clicked.connect(lambda _, d=data: self._on_monitor_clicked(d))

    def add_respondent(self, data: dict):
        """Public: tambahkan responden baru ke data dan refresh tabel."""
        self._all_data.append(data)
        self._apply_filters()

    # ── Filters ──────────────────────────────────────────────────────────────
    def _apply_filters(self):
        query         = self.search_bar.text().strip().lower()
        status_filter = self.filter_combo.currentText()

        filtered = [
            d for d in self._all_data
            if query in d["nama"].lower()
            and (status_filter == "Semua Status" or d["status"] == status_filter)
        ]
        self._populate_table(filtered)

    # ── Navigation ────────────────────────────────────────────────────────────
    def _on_monitor_clicked(self, data: dict):
        self.navigate_to_monitoring.emit(data)

    # ── Dialog ────────────────────────────────────────────────────────────────
    def _open_add_dialog(self):
        dlg = RespondentDialog(self)
        dlg.respondent_added.connect(self.add_respondent)
        dlg.exec()
