"""
widgets/respondent_dialog.py
Modal dialog untuk menambah responden baru.

Revisi & Perbaikan:
- Menghapus conflict stylesheet lokal yang menabrak styles.qss global.
- Menambahkan objectName secara tepat agar mendeteksi selector global (#PrimaryBtn & #GhostBtn).
- Mengunci posisi tombol di layout utama terbawah agar tidak terpotong QScrollArea.
"""

import uuid
from PySide6.QtWidgets import (
    QDialog,
    QVBoxLayout,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QPushButton,
    QFrame,
    QButtonGroup,
    QWidget,
    QDateEdit,
    QScrollArea,
)
from PySide6.QtCore import Qt, Signal, QDate


# -- ToggleChip --------------------------------------------------------------
class ToggleChip(QPushButton):
    """
    Tombol chip bergaya segmented control khusus untuk Jenis Kelamin.
    """

    def __init__(self, label: str, parent=None):
        super().__init__(parent)
        self.setText(label)
        self.setCheckable(True)
        self.setCursor(Qt.PointingHandCursor)
        self.setMinimumHeight(38)
        self.setMinimumWidth(120)
        self._refresh_style()
        self.toggled.connect(self._refresh_style)

    def _refresh_style(self):
        if self.isChecked():
            self.setText(f"✓  {self.text().replace('✓  ', '')}")
            self.setStyleSheet(
                "QPushButton {"
                "  background-color: #3E6E63; color: #FFFFFF;"
                "  border: 1px solid #3E6E63; border-radius: 8px;"
                "  font-size: 14px; font-weight: 700; text-align: center;"
                "}"
            )
        else:
            self.setText(self.text().replace("✓  ", ""))
            self.setStyleSheet(
                "QPushButton {"
                "  background-color: transparent; color: #6B7A99;"
                "  border: 1px solid #D1D8E5; border-radius: 8px;"
                "  font-size: 14px; font-weight: 500; text-align: center;"
                "}"
                "QPushButton:hover {"
                "  background-color: #F8FAFC; border-color: #A0AEC0;"
                "}"
            )

    def value(self) -> str:
        return self.text().replace("✓  ", "").strip()


# -- RespondentDialog ---------------------------------------------------------
class RespondentDialog(QDialog):
    """
    Dialog form pop-up untuk pendaftaran responden baru beserta diagnosis/status klinis awal.
    """

    respondent_added = Signal(dict)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Tambah Responden Baru")
        self.setModal(True)
        self.setMinimumSize(550, 600)
        
        # Biarkan background mengikuti styles.qss global agar sinkron hangat clean neutral.
        self.setObjectName("RespondentDialog") 

        self._build_ui()

    def _build_ui(self):
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(28, 28, 28, 28)
        main_layout.setSpacing(0)

        # -- Header -----------------------------------------------------------
        header_lbl = QLabel("Registrasi Responden")
        header_lbl.setStyleSheet("font-size: 22px; font-weight: 800; color: #1A2340; background: transparent;")
        main_layout.addWidget(header_lbl)

        sub_lbl = QLabel("Silakan lengkapi data identitas dan kondisi awal responden dibawah ini.")
        sub_lbl.setStyleSheet("font-size: 13px; color: #6B7A99; margin-top: 4px; background: transparent;")
        main_layout.addWidget(sub_lbl)

        main_layout.addSpacing(16)

        div_top = QFrame()
        div_top.setFrameShape(QFrame.HLine)
        div_top.setObjectName("HDivider") # Sesuai dengan spesifikasi styles.qss Anda
        main_layout.addWidget(div_top)

        # -- Scroll Area Content ----------------------------------------------
        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)
        scroll_area.setFrameShape(QFrame.NoFrame)
        scroll_area.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        scroll_area.setVerticalScrollBarPolicy(Qt.ScrollBarAsNeeded)
        scroll_area.setStyleSheet("QScrollArea { background-color: transparent; }")

        form_widget = QWidget()
        form_widget.setStyleSheet("background-color: transparent;")
        form_layout = QVBoxLayout(form_widget)
        form_layout.setContentsMargins(4, 16, 4, 16)
        form_layout.setSpacing(18)

        # 1. Nama Lengkap Input
        nama_container = QVBoxLayout()
        nama_container.setSpacing(6)
        nama_lbl = QLabel("NAMA LENGKAP")
        nama_lbl.setStyleSheet("font-size: 11px; font-weight: 700; color: #4A5568; letter-spacing: 0.5px;")
        
        self.nama_input = QLineEdit()
        self.nama_input.setPlaceholderText("Masukkan nama lengkap responden...")
        self.nama_input.setMinimumHeight(42)
        
        nama_container.addWidget(nama_lbl)
        nama_container.addWidget(self.nama_input)
        form_layout.addLayout(nama_container)

        # 2. Tanggal Lahir Input
        tgl_container = QVBoxLayout()
        tgl_container.setSpacing(6)
        tgl_lbl = QLabel("TANGGAL LAHIR")
        tgl_lbl.setStyleSheet("font-size: 11px; font-weight: 700; color: #4A5568; letter-spacing: 0.5px;")
        
        self.tanggal_lahir_input = QDateEdit()
        self.tanggal_lahir_input.setCalendarPopup(True)
        self.tanggal_lahir_input.setDisplayFormat("yyyy-MM-dd")
        self.tanggal_lahir_input.setMinimumHeight(42)
        self.tanggal_lahir_input.setDate(QDate.currentDate().addYears(-20))
        self.tanggal_lahir_input.setMinimumDate(QDate(1920, 1, 1))
        self.tanggal_lahir_input.setMaximumDate(QDate.currentDate())
        
        tgl_container.addWidget(tgl_lbl)
        tgl_container.addWidget(self.tanggal_lahir_input)
        form_layout.addLayout(tgl_container)

        # 3. Jenis Kelamin Input
        jk_container = QVBoxLayout()
        jk_container.setSpacing(6)
        jk_lbl = QLabel("JENIS KELAMIN")
        jk_lbl.setStyleSheet("font-size: 11px; font-weight: 700; color: #4A5568; letter-spacing: 0.5px;")
        
        jk_row = QHBoxLayout()
        jk_row.setSpacing(12)
        
        self.chip_laki = ToggleChip("Laki-Laki")
        self.chip_perempuan = ToggleChip("Perempuan")
        self.chip_laki.setChecked(True)
        
        self._jk_group = QButtonGroup(self)
        self._jk_group.addButton(self.chip_laki, 0)
        self._jk_group.addButton(self.chip_perempuan, 1)
        
        jk_row.addWidget(self.chip_laki)
        jk_row.addWidget(self.chip_perempuan)
        jk_row.addStretch()
        
        jk_container.addWidget(jk_lbl)
        jk_container.addLayout(jk_row)
        form_layout.addLayout(jk_container)

        # 4. Status / Diagnosis Input
        status_container = QVBoxLayout()
        status_container.setSpacing(6)
        status_lbl = QLabel("STATUS / DIAGNOSIS AWAL (MAKSIMAL 20 KARAKTER)")
        status_lbl.setStyleSheet("font-size: 11px; font-weight: 700; color: #4A5568; letter-spacing: 0.5px;")
        
        self.status_input = QLineEdit()
        self.status_input.setPlaceholderText("Contoh: Normal, Flat Foot, Clubfoot, Genu Varum, dll.")
        self.status_input.setMinimumHeight(42)
        self.status_input.setMaxLength(20)
        
        status_container.addWidget(status_lbl)
        status_container.addWidget(self.status_input)
        form_layout.addLayout(status_container)

        scroll_area.setWidget(form_widget)
        main_layout.addWidget(scroll_area)

        # Divider line bawah
        div_bottom = QFrame()
        div_bottom.setFrameShape(QFrame.HLine)
        div_bottom.setObjectName("HDivider") # Sesuai dengan spesifikasi styles.qss Anda
        main_layout.addWidget(div_bottom)
        main_layout.addSpacing(16)

        # -- Action Buttons (Terkoneksi langsung ke styles.qss global) ---------
        btn_row = QHBoxLayout()
        btn_row.setSpacing(12)
        
        cancel_btn = QPushButton("Batal")
        cancel_btn.setObjectName("GhostBtn")  # Membaca style dari styles.qss
        cancel_btn.setMinimumHeight(40)
        cancel_btn.setMinimumWidth(110)
        cancel_btn.setCursor(Qt.PointingHandCursor)
        cancel_btn.clicked.connect(self.reject)

        save_btn = QPushButton("Simpan Responden")
        save_btn.setObjectName("PrimaryBtn")  # Membaca style dari styles.qss
        save_btn.setMinimumHeight(40)
        save_btn.setMinimumWidth(170)
        save_btn.setCursor(Qt.PointingHandCursor)
        save_btn.clicked.connect(self._save)

        btn_row.addStretch()
        btn_row.addWidget(cancel_btn)
        btn_row.addWidget(save_btn)
        main_layout.addLayout(btn_row)

        # Style input form lokal agar rapi dan teksnya terlihat jelas di latar neutral
        self.setStyleSheet(
            "QLineEdit, QDateEdit {"
            "  border: 1px solid #C7C4B7;"
            "  border-radius: 8px;"
            "  padding: 0px 12px;"
            "  background-color: #F8F9F6;"
            "  font-size: 14px;"
            "  color: #1A2340;"
            "}"
            "QLineEdit:focus, QDateEdit:focus {"
            "  border: 2px solid #3E6E63;"
            "  background-color: #FFFFFF;"
            "}"
        )

    # -- Save & Validation ----------------------------------------------------
    def _save(self):
        nama = self.nama_input.text().strip()
        if not nama:
            self.nama_input.setStyleSheet(
                "border: 2px solid #E74C3C; border-radius: 8px; padding: 0px 12px;"
                " background: #FFF6F6; font-size: 14px;"
            )
            self.nama_input.setPlaceholderText("Nama tidak boleh kosong!")
            self.nama_input.setFocus()
            return

        status = self.status_input.text().strip()
        if not status:
            status = "Normal"

        tanggal_lahir = self.tanggal_lahir_input.date().toString("yyyy-MM-dd")
        jk = self.chip_laki.value() if self._jk_group.checkedId() == 0 else self.chip_perempuan.value()

        # Otomatisasi generate UID acak agar sukses masuk primary key database Laragon
        generated_uid = f"USR-{uuid.uuid4().hex[:8].upper()}"

        # Kirim data ke main_page controller
        self.respondent_added.emit(
            {
                "uid": generated_uid,
                "nama": nama,
                "tanggal_lahir": tanggal_lahir,
                "jenis_kelamin": jk,
                "status": status,
            }
        )
        self.accept()