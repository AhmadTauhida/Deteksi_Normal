"""
pages/main_page.py
Main page — Daftar Responden dengan background putih clean bawaan asli.
Mengambil data langsung dari MySQL db_ankle_analysis.
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
from datetime import date, datetime

from widgets.status_badge import StatusBadge
from widgets.respondent_dialog import RespondentDialog
# 🚀 IMPORT DATABASE MANAGER
from database.database_manager import DatabaseManager

# Konstanta kolom tabel
COL_UID = 0
COL_NAMA = 1
COL_UMUR = 2
COL_JK = 3
COL_STATUS = 4
COL_AKSI = 5


def hitung_usia(tanggal_lahir_obj) -> int:
    """Mengubah tanggal_lahir dari database menjadi umur dinamis tahun ini (2026)."""
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
    Main page — Menampilkan daftar responden dengan gaya clean background putih.
    """

    navigate_to_monitoring = Signal(dict)

    def __init__(self, parent=None):
        super().__init__(parent)
        
        # 🚀 INISIALISASI DATABASE MANAGER
        self.db = DatabaseManager()
        
        # Ambil data dari MySQL
        self._all_data: list[dict] = self.db.get_all_respondents()

        self._build_ui()
        self._populate_table(self._all_data)

    # ── UI Construction (Mempertahankan Style Putih Bersih Asli) ──────────────
    def _build_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(24, 24, 24, 24)
        layout.setSpacing(20)

        # Header Section
        header_layout = QHBoxLayout()
        header_title = QLabel("Daftar Responden")
        header_title.setFont(QFont("Segoe UI", 22, QFont.Bold))
        header_title.setStyleSheet("color: #1E293B; background: transparent;")  # Teks gelap untuk bg putih

        add_btn = QPushButton("➕  Tambah Responden")
        add_btn.setCursor(Qt.PointingHandCursor)
        add_btn.setStyleSheet(
            "QPushButton { background-color: #2D7DD2; color: white; font-weight: bold; "
            "border-radius: 8px; padding: 10px 18px; font-size: 13px; border: none; }"
            "QPushButton:hover { background-color: #1F61A9; }"
        )
        add_btn.clicked.connect(self._on_add_clicked)

        header_layout.addWidget(header_title)
        header_layout.addStretch()
        header_layout.addWidget(add_btn)
        layout.addLayout(header_layout)

        # Filter & Search Controls Frame (Style Putih Clean)
        filter_frame = QFrame()
        filter_frame.setStyleSheet(
            "QFrame { background-color: #F8FAFC; border: 1px solid #E2E8F0; border-radius: 12px; }"
        )
        filter_layout = QHBoxLayout(filter_frame)
        filter_layout.setContentsMargins(16, 12, 16, 12)
        filter_layout.setSpacing(14)

        self.search_bar = QLineEdit()
        self.search_bar.setPlaceholderText("🔍  Cari nama responden...")
        self.search_bar.setStyleSheet(
            "QLineEdit { background-color: #FFFFFF; color: #1E293B; border: 1px solid #CBD5E1; "
            "border-radius: 6px; padding: 8px 12px; font-size: 13px; }"
            "QLineEdit:focus { border: 1px solid #2D7DD2; }"
        )
        self.search_bar.textChanged.connect(self._apply_filters)

        self.filter_combo = QComboBox()
        self.filter_combo.addItems(["Semua Status", "Normal", "Tidak Normal"])
        self.filter_combo.setStyleSheet(
            "QComboBox { background-color: #FFFFFF; color: #1E293B; border: 1px solid #CBD5E1; "
            "border-radius: 6px; padding: 7px 12px; font-size: 13px; min-width: 140px; }"
        )
        self.filter_combo.currentTextChanged.connect(self._apply_filters)

        filter_layout.addWidget(self.search_bar, stretch=1)
        filter_layout.addWidget(self.filter_combo)
        layout.addWidget(filter_frame)

        # Table Section (Style Putih Clean)
        self.table = QTableWidget()
        self.table.setColumnCount(6)
        self.table.setHorizontalHeaderLabels(["UID", "Nama", "Usia", "Jenis Kelamin", "Status Ankle", "Aksi"])
        
        self.table.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.table.setEditTriggers(QAbstractItemView.NoEditTriggers)
        self.table.setFocusPolicy(Qt.NoFocus)
        self.table.setAlternatingRowColors(True)

        self.table.setStyleSheet(
            "QTableWidget { background-color: #FFFFFF; color: #334155; gridline-color: #E2E8F0; "
            "border: 1px solid #E2E8F0; border-radius: 12px; font-size: 13px; alternate-background-color: #F8FAFC; }"
            "QHeaderView::section { background-color: #F1F5F9; color: #475569; font-weight: bold; "
            "padding: 12px; border: none; border-bottom: 2px solid #E2E8F0; font-size: 12px; }"
            "QTableWidget::item { padding: 12px; }"
        )

        header = self.table.horizontalHeader()
        header.setSectionResizeMode(COL_UID, QHeaderView.ResizeToContents)
        header.setSectionResizeMode(COL_NAMA, QHeaderView.Stretch)
        header.setSectionResizeMode(COL_UMUR, QHeaderView.ResizeToContents)
        header.setSectionResizeMode(COL_JK, QHeaderView.ResizeToContents)

        # PENTING: kolom Status & Aksi berisi cell widget (badge/tombol), bukan teks biasa.
        # ResizeToContents tidak reliable untuk cell widget karena sizeHint() widget
        # belum ter-compute saat kolom pertama kali dibuat, sehingga kolom bisa
        # collapse ke lebar ~0 dan widget jadi tidak terlihat. Gunakan lebar tetap.
        header.setSectionResizeMode(COL_STATUS, QHeaderView.Fixed)
        self.table.setColumnWidth(COL_STATUS, 150)
        header.setSectionResizeMode(COL_AKSI, QHeaderView.Fixed)
        self.table.setColumnWidth(COL_AKSI, 190)

        self.table.verticalHeader().setVisible(False)
        layout.addWidget(self.table)

    # ── Table Population ──────────────────────────────────────────────────────
    def _populate_table(self, data_list: list[dict]):
        self.table.setRowCount(0)
        self.table.setRowCount(len(data_list))

        for row, data in enumerate(data_list):
            self.table.setRowHeight(row, 56)

            # Normalisasi Key dari Database agar match dengan kebutuhan komponen UI
            uid = data.get("uid", "")
            nama = data.get("nama", "")
            tgl_lahir = data.get("tanggal_lahir")
            usia = hitung_usia(tgl_lahir)
            jk = data.get("jenis_kelamin", "")
            status_str = data.get("status", "Normal")

            # 1. Kolom UID
            uid_item = QTableWidgetItem(str(uid))
            uid_item.setTextAlignment(Qt.AlignCenter)
            self.table.setItem(row, COL_UID, uid_item)

            # 2. Kolom Nama
            self.table.setItem(row, COL_NAMA, QTableWidgetItem(nama))

            # 3. Kolom Usia
            usia_text = f"{usia} tahun" if usia > 0 else "—"
            usia_item = QTableWidgetItem(usia_text)
            usia_item.setTextAlignment(Qt.AlignCenter)
            self.table.setItem(row, COL_UMUR, usia_item)

            # 4. Kolom Jenis Kelamin
            jk_item = QTableWidgetItem(jk)
            jk_item.setTextAlignment(Qt.AlignCenter)
            self.table.setItem(row, COL_JK, jk_item)

            # 5. Kolom Status Ankle (SEKARANG MUNCUL SEMPURNA)
            badge_container = QWidget()
            badge_container.setStyleSheet("background: transparent;")
            badge_layout = QHBoxLayout(badge_container)
            badge_layout.setContentsMargins(6, 6, 6, 6)
            badge_layout.setAlignment(Qt.AlignCenter)

            # Memastikan format data dikirim ke StatusBadge dengan benar
            badge = StatusBadge(status_str)
            badge.setMinimumWidth(110)
            badge_layout.addWidget(badge)
            self.table.setCellWidget(row, COL_STATUS, badge_container)

            # 6. Kolom Aksi (SEKARANG MUNCUL SEMPURNA)
            monitor_btn = QPushButton("Buka Sesi Monitoring  ➔")
            monitor_btn.setCursor(Qt.PointingHandCursor)
            monitor_btn.setMinimumWidth(170)
            monitor_btn.setStyleSheet(
                "QPushButton { background-color: #10B981; color: white; font-weight: bold; "
                "border: none; border-radius: 6px; font-size: 11px; padding: 6px 14px; }"
                "QPushButton:hover { background-color: #059669; }"
            )

            btn_container = QWidget()
            btn_container.setStyleSheet("background: transparent;")
            btn_layout = QHBoxLayout(btn_container)
            btn_layout.setContentsMargins(8, 6, 8, 6)
            btn_layout.addWidget(monitor_btn)
            self.table.setCellWidget(row, COL_AKSI, btn_container)
            
            # Format data terstandarisasi untuk dilempar ke monitoring_page.py
            monitor_data = {
                "uid": uid,
                "nama": nama,
                "umur": usia,
                "jenis_kelamin": jk,
                "status": status_str
            }
            monitor_btn.clicked.connect(lambda _, d=monitor_data: self._on_monitor_clicked(d))

    # ── Actions ──────────────────────────────────────────────────────────────
    def _on_add_clicked(self):
        """Membuka Dialog input responden baru dan menyimpan ke MySQL."""
        dialog = RespondentDialog(self)
        if dialog.exec():
            new_resp = dialog.get_data()
            
            # Buat format UID baru otomatis
            new_uid = f"R{len(self._all_data) + 1:03d}"
            
            # Konversi umur masukan menjadi tanggal lahir perkiraan (Tahun 2026 - Umur)
            tahun_lahir = 2026 - int(new_resp.get("Umur", new_resp.get("umur", 0)))
            tanggal_lahir_formatted = f"{tahun_lahir}-01-01"

            # Simpan ke MySQL via DatabaseManager
            berhasil = self.db.add_respondent(
                uid=new_uid,
                nama=new_resp.get("Nama", new_resp.get("nama", "")),
                tanggal_lahir=tanggal_lahir_formatted,
                jenis_kelamin=new_resp.get("Jenis Kelamin", new_resp.get("jenis_kelamin", "")),
                status=new_resp.get("Status", new_resp.get("status", "Normal"))
            )
            
            if berhasil:
                self._all_data = self.db.get_all_respondents()
                self._apply_filters()

    # ── Filters ──────────────────────────────────────────────────────────────
    def _apply_filters(self):
        query = self.search_bar.text().strip().lower()
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