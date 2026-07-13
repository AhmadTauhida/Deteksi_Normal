"""
pages/main_page.py
Main page — Daftar Responden dengan search, filter, tabel, dan tombol tambah.
Revisi 2: Nama center, badge status tanpa kotak, jenis kelamin tanpa ikon,
tombol Monitoring lebih menonjol dan mudah dikenali.
Revisi 3: Data diambil langsung dari MySQL (db_ankle_analysis) via DatabaseManager,
tidak lagi memakai data dummy.
"""

from __future__ import annotations

from datetime import date, datetime

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
    QSizePolicy,
)
from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QFont, QIcon

from widgets.status_badge import StatusBadge
from widgets.respondent_dialog import RespondentDialog

# 🚀 IMPORT DATABASE MANAGER
from database.database_manager import DatabaseManager

COL_NAMA, COL_UMUR, COL_JK, COL_STATUS, COL_AKSI = 0, 1, 2, 3, 4

# Lebar tetap kolom non-stretch (px) — cukup untuk konten terpanjang
COL_UMUR_W   = 90    # "60 thn" → cukup 90
COL_JK_W     = 130   # "Perempuan" (tanpa ikon) → 130
COL_STATUS_W = 130   # "Tidak Normal" teks polos → 130
COL_AKSI_W   = 190   # tombol Monitoring baru, lebih lega → 190 (cukup untuk ikon + teks + padding)


def hitung_usia(tanggal_lahir_obj) -> int:
    """Mengubah tanggal_lahir dari database menjadi umur dinamis tahun ini."""
    if not tanggal_lahir_obj:
        return 0
    hari_ini = date.today()
    if isinstance(tanggal_lahir_obj, str):
        try:
            tanggal_lahir_obj = datetime.strptime(tanggal_lahir_obj, "%Y-%m-%d").date()
        except ValueError:
            return 0
    usia = hari_ini.year - tanggal_lahir_obj.year
    belum_ulang_tahun = (hari_ini.month, hari_ini.day) < (tanggal_lahir_obj.month, tanggal_lahir_obj.day)
    if belum_ulang_tahun:
        usia -= 1
    return usia


class MainPage(QWidget):
    """
    Halaman utama berisi daftar responden.

    Signals:
        navigate_to_monitoring (dict): Emitted when user clicks Monitoring button.
    """

    navigate_to_monitoring = Signal(dict)

    def __init__(self, parent=None):
        super().__init__(parent)

        # 🚀 Koneksi ke MySQL
        self.db = DatabaseManager()
        self._all_data: list[dict] = self.db.get_all_respondents()

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
        # Header tetap center supaya konsisten dengan isi kolom
        hdr.setDefaultAlignment(Qt.AlignCenter)

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
        self.table.verticalHeader().setDefaultSectionSize(60)

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

        total    = len(self._all_data)
        normal   = sum(1 for d in self._all_data if d.get("status") == "Normal")
        abnormal = total - normal
        self.total_label.setText(
            f"Total: {total}  •  Normal: {normal}  •  Tidak Normal: {abnormal}"
        )

    def _insert_row(self, data: dict):
        row = self.table.rowCount()
        self.table.insertRow(row)
        self.table.setRowHeight(row, 60)

        uid       = data.get("uid", "")
        nama      = data.get("nama", "")
        umur      = hitung_usia(data.get("tanggal_lahir"))
        jk        = data.get("jenis_kelamin", "")
        status    = data.get("status", "Normal")

        # ── Nama (center, bukan rata kiri) ──────────────────────────────
        nama_item = QTableWidgetItem(nama)
        nama_item.setFont(QFont("Segoe UI", 13, QFont.Medium))
        nama_item.setTextAlignment(Qt.AlignCenter)
        nama_item.setData(Qt.UserRole, data)
        nama_item.setToolTip(nama)
        self.table.setItem(row, COL_NAMA, nama_item)

        # ── Umur ─────────────────────────────────────────────────────────
        umur_text = f"{umur} thn" if umur > 0 else "—"
        umur_item = QTableWidgetItem(umur_text)
        umur_item.setTextAlignment(Qt.AlignCenter)
        self.table.setItem(row, COL_UMUR, umur_item)

        # ── Jenis Kelamin (teks polos, tanpa ikon ♂/♀) ───────────────────
        jk_item = QTableWidgetItem(jk)
        jk_item.setTextAlignment(Qt.AlignCenter)
        self.table.setItem(row, COL_JK, jk_item)

        # ── Status (teks berwarna polos, tanpa kotak/border) ─────────────
        badge = StatusBadge(status)
        badge_container = QWidget()
        badge_container.setStyleSheet("background: transparent;")
        bc_layout = QHBoxLayout(badge_container)
        bc_layout.setContentsMargins(0, 0, 0, 0)
        bc_layout.addWidget(badge, alignment=Qt.AlignCenter)
        self.table.setCellWidget(row, COL_STATUS, badge_container)

        # ── Aksi: tombol Monitoring (lebih menonjol & mudah dikenali) ────
        monitor_btn = QPushButton("▶  Monitoring")
        monitor_btn.setObjectName("MonitorBtn")
        monitor_btn.setCursor(Qt.PointingHandCursor)
        monitor_btn.setFixedHeight(36)
        monitor_btn.setFixedWidth(130)
        monitor_btn.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Fixed)
        # Inline style sebagai jaminan tampilan (tidak bergantung penuh pada
        # cascade QSS global, supaya tombol pasti terlihat solid & jelas
        # sebagai tombol, bukan teks biasa).
        monitor_btn.setStyleSheet(
            """
            QPushButton {
                background-color: #3E6E63;
                color: #FFFFFF;
                border: none;
                border-radius: 8px;
                padding: 8px 16px;
                font-size: 13px;
                font-weight: 700;
            }
            QPushButton:hover {
                background-color: #335A51;
            }
            QPushButton:pressed {
                background-color: #24413B;
            }
            """
        )

        btn_container = QWidget()
        btn_container.setStyleSheet("background: transparent;")
        btn_layout = QHBoxLayout(btn_container)
        btn_layout.setContentsMargins(6, 0, 6, 0)
        btn_layout.addWidget(monitor_btn, alignment=Qt.AlignCenter)
        self.table.setCellWidget(row, COL_AKSI, btn_container)

        # Payload untuk monitoring_page.py — key HARUS lowercase supaya
        # cocok dengan monitoring_page.set_respondent() yang membaca
        # data.get("nama"/"umur"/"jenis_kelamin"/"status").
        monitor_data = {
            "uid": uid,
            "nama": nama,
            "umur": umur,
            "jenis_kelamin": jk,
            "status": status,
        }
        monitor_btn.clicked.connect(lambda _, d=monitor_data: self._on_monitor_clicked(d))

    def add_respondent(self, data: dict):
        """
        Callback dari RespondentDialog.respondent_added.
        Simpan responden baru ke MySQL, lalu refresh tabel dari database
        (bukan sekadar append ke list lokal) supaya UID & data selalu
        sinkron dengan sumber kebenaran (database).
        """
        nama          = data.get("nama", "")
        tanggal_lahir = data.get("tanggal_lahir", "")
        jk            = data.get("jenis_kelamin", "")
        status        = data.get("status", "Normal")

        new_uid = f"R{len(self._all_data) + 1:03d}"

        berhasil = self.db.add_respondent(
            uid=new_uid,
            nama=nama,
            tanggal_lahir=tanggal_lahir,
            jenis_kelamin=jk,
            status=status,
        )

        if berhasil:
            self._all_data = self.db.get_all_respondents()
            self._apply_filters()
        else:
            print("[MainPage] Gagal menyimpan responden baru ke database.")

    # ── Filters ──────────────────────────────────────────────────────────────
    def _apply_filters(self):
        query         = self.search_bar.text().strip().lower()
        status_filter = self.filter_combo.currentText()

        filtered = [
            d for d in self._all_data
            if query in d.get("nama", "").lower()
            and (status_filter == "Semua Status" or d.get("status", "") == status_filter)
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