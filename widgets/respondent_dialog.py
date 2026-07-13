"""
widgets/respondent_dialog.py

"""

from PySide6.QtWidgets import (
    QDialog,
    QVBoxLayout,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QSpinBox,
    QPushButton,
    QFrame,
    QButtonGroup,
    QWidget,
    QScrollArea,
)
from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QFont, QIntValidator


# ── SuffixLineEdit ────────────────────────────────────────────────────────────
class SuffixLineEdit(QLineEdit):
    """
    QLineEdit dengan label suffix (mis. "tahun") yang tampil menempel
    di dalam kotak, di sisi kanan — mirip suffix pada QSpinBox, tapi
    tetap mempertahankan behaviour QLineEdit biasa (placeholder hilang
    otomatis saat mulai mengetik, tanpa perlu hapus dulu).
    """

    def __init__(self, suffix_text: str, parent=None):
        super().__init__(parent)
        self._suffix_label = QLabel(suffix_text, self)
        self._suffix_label.setStyleSheet(
            "color: #9AA3B8; font-size: 13px; font-weight: 500; background: transparent;"
        )
        self._suffix_label.setAttribute(Qt.WA_TransparentForMouseEvents)
        self._update_text_margin()

    def _update_text_margin(self):
        self._suffix_label.adjustSize()
        margin = self._suffix_label.width() + 20
        self.setTextMargins(0, 0, margin, 0)

    def resizeEvent(self, event):
        super().resizeEvent(event)
        self._reposition_suffix()

    def _reposition_suffix(self):
        self._suffix_label.adjustSize()
        x = self.width() - self._suffix_label.width() - 14
        y = (self.height() - self._suffix_label.height()) // 2
        self._suffix_label.move(x, y)


# -- ToggleChip ---------------------------------------------------------------
class ToggleChip(QPushButton):
    """
    Tombol chip bergaya segmented control.
    Menampilkan tanda centang (checkmark) dan background biru saat dipilih.
    Saat tidak dipilih: border outline saja.
    """

    def __init__(self, label: str, parent=None):
        super().__init__(parent)
        self.setText(label)
        self.setCheckable(True)
        self.setCursor(Qt.PointingHandCursor)
        self.setMinimumHeight(40)
        self.setMinimumWidth(120)
        self._refresh_style()
        self.toggled.connect(self._refresh_style)

    # ------------------------------------------------------------------
    def _refresh_style(self):
        if self.isChecked():
            self.setStyleSheet(
                "QPushButton {"
                "  background-color: #3E6E63;"
                "  color: #FFFFFF;"
                "  border: 2px solid #3E6E63;"
                "  border-radius: 10px;"
                "  padding: 8px 20px;"
                "  font-size: 13px;"
                "  font-weight: 700;"
                "  text-align: center;"
                "}"
                "QPushButton:hover {"
                "  background-color: #335A51;"
                "  border-color: #335A51;"
                "}"
            )
            self.setText(f"\u2713  {self._base_label()}")
        else:
            self.setStyleSheet(
                "QPushButton {"
                "  background-color: #F8F9F6;"
                "  color: #4A5568;"
                "  border: 1.5px solid #C7C4B7;"
                "  border-radius: 10px;"
                "  padding: 8px 20px;"
                "  font-size: 13px;"
                "  font-weight: 500;"
                "  text-align: center;"
                "}"
                "QPushButton:hover {"
                "  background-color: #E7F0ED;"
                "  border-color: #3E6E63;"
                "  color: #3E6E63;"
                "}"
            )
            self.setText(self._base_label())

    def _base_label(self) -> str:
        """Kembalikan label bersih tanpa prefix centang."""
        txt = self.text()
        if txt.startswith("\u2713  "):
            return txt[3:]
        return txt

    def value(self) -> str:
        """Kembalikan nilai label tanpa prefix centang."""
        return self._base_label()


# -- RespondentDialog ----------------------------------------------------------
class RespondentDialog(QDialog):
    """
    Dialog input data responden baru.
    Emits `respondent_added(dict)` saat user klik Simpan.
    """

    respondent_added = Signal(dict)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Tambah Responden Baru")
        # Diturunkan dari (520, 560) -> (420, 380) supaya dialog masih
        # bisa di-resize kecil secara wajar; konten yang kepanjangan akan
        # otomatis scroll (lihat QScrollArea di _build_ui).
        self.setMinimumSize(420, 380)
        self.resize(560, 600)
        self.setObjectName("AppRoot")
        self._build_ui()

    # ------------------------------------------------------------------
    def _build_ui(self):
        outer = QVBoxLayout(self)
        outer.setContentsMargins(16, 16, 16, 16)
        outer.setSpacing(0)

        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.NoFrame)

        card = QFrame()
        card.setObjectName("DialogCard")
        card_layout = QVBoxLayout(card)
        card_layout.setContentsMargins(32, 28, 32, 28)
        card_layout.setSpacing(0)          # spacing diatur manual per section

        # -- Header ---------------------------------------------------------
        header_row = QHBoxLayout()
        header_row.setSpacing(14)

        icon_lbl = QLabel("\U0001F464")
        icon_lbl.setFixedSize(44, 44)
        icon_lbl.setAlignment(Qt.AlignCenter)
        icon_lbl.setStyleSheet(
            "font-size: 26px; background: #EBF4FF; border-radius: 22px;"
        )
        header_row.addWidget(icon_lbl)

        title_col = QVBoxLayout()
        title_col.setSpacing(3)
        t = QLabel("Tambah Responden")
        t.setStyleSheet(
            "font-size: 18px; font-weight: 700; color: #1A2340; background: transparent;"
        )
        s = QLabel("Isi data responden baru di bawah ini.")
        s.setStyleSheet(
            "font-size: 12px; color: #9AA3B8; background: transparent;"
        )
        title_col.addWidget(t)
        title_col.addWidget(s)
        header_row.addLayout(title_col)
        header_row.addStretch()

        close_btn = QPushButton("\u2715")
        close_btn.setFixedSize(32, 32)
        close_btn.setStyleSheet(
            "QPushButton { background: #F0F2F8; border: none; border-radius: 16px;"
            " color: #6B7A99; font-size: 14px; font-weight: 600; }"
            "QPushButton:hover { background: #E0E4EF; color: #1A2340; }"
        )
        close_btn.clicked.connect(self.reject)
        header_row.addWidget(close_btn)

        card_layout.addLayout(header_row)
        card_layout.addSpacing(20)

        # -- Divider ----------------------------------------------------------
        card_layout.addWidget(self._divider())
        card_layout.addSpacing(22)

        # -- Nama Lengkap -------------------------------------------------------
        card_layout.addWidget(self._field_label("Nama Lengkap"))
        card_layout.addSpacing(6)

        self.nama_input = QLineEdit()
        self.nama_input.setPlaceholderText("Masukkan nama lengkap responden...")
        self.nama_input.setFixedHeight(44)
        self.nama_input.setMinimumWidth(220)
        card_layout.addWidget(self.nama_input)
        card_layout.addSpacing(18)

        # -- Umur -----------------------------------------------------------------
        card_layout.addWidget(self._field_label("Umur"))
        card_layout.addSpacing(6)

        umur_row = QHBoxLayout()
        umur_row.setSpacing(12)

        self.umur_input = SuffixLineEdit("tahun")
        self.umur_input.setPlaceholderText("Masukkan umur")
        self.umur_input.setValidator(QIntValidator(1, 150, self))
        self.umur_input.setFixedHeight(44)
        self.umur_input.setMinimumWidth(160)
        umur_row.addWidget(self.umur_input)
        umur_row.addStretch()
        card_layout.addLayout(umur_row)
        card_layout.addSpacing(18)

        # -- Jenis Kelamin (ToggleChip) --------------------------------------------
        card_layout.addWidget(self._field_label("Jenis Kelamin"))
        card_layout.addSpacing(8)

        jk_row = QHBoxLayout()
        jk_row.setSpacing(10)
        jk_row.setContentsMargins(0, 0, 0, 0)

        self.chip_laki     = ToggleChip("Laki-laki")
        self.chip_perempuan = ToggleChip("Perempuan")
        self.chip_laki.setChecked(True)

        self._jk_group = QButtonGroup(self)
        self._jk_group.setExclusive(True)
        self._jk_group.addButton(self.chip_laki,      0)
        self._jk_group.addButton(self.chip_perempuan, 1)

        jk_row.addWidget(self.chip_laki)
        jk_row.addWidget(self.chip_perempuan)
        jk_row.addStretch()
        card_layout.addLayout(jk_row)
        card_layout.addSpacing(18)

        # -- Status Awal (ToggleChip) ------------------------------------------------
        card_layout.addWidget(self._field_label("Status Awal"))
        card_layout.addSpacing(8)

        st_row = QHBoxLayout()
        st_row.setSpacing(10)
        st_row.setContentsMargins(0, 0, 0, 0)

        self.chip_normal   = ToggleChip("Normal")
        self.chip_abnormal = ToggleChip("Tidak Normal")
        self.chip_normal.setChecked(True)

        # Chip abnormal gunakan warna oranye/merah saat aktif
        self.chip_abnormal.toggled.connect(self._style_abnormal_chip)
        self.chip_normal.toggled.connect(self._style_normal_chip)

        self._status_group = QButtonGroup(self)
        self._status_group.setExclusive(True)
        self._status_group.addButton(self.chip_normal,   0)
        self._status_group.addButton(self.chip_abnormal, 1)

        st_row.addWidget(self.chip_normal)
        st_row.addWidget(self.chip_abnormal)
        st_row.addStretch()
        card_layout.addLayout(st_row)

        card_layout.addSpacing(22)

        # -- Divider ----------------------------------------------------------
        card_layout.addWidget(self._divider())
        card_layout.addSpacing(20)

        # -- Action buttons ------------------------------------------------------
        btn_row = QHBoxLayout()
        btn_row.setSpacing(12)

        cancel_btn = QPushButton("Batal")
        cancel_btn.setObjectName("GhostBtn")
        cancel_btn.setFixedHeight(44)
        cancel_btn.setMinimumWidth(100)
        cancel_btn.clicked.connect(self.reject)

        save_btn = QPushButton("\U0001F4BE  Simpan Responden")
        save_btn.setObjectName("PrimaryBtn")
        save_btn.setFixedHeight(44)
        save_btn.setMinimumWidth(170)
        save_btn.clicked.connect(self._save)

        btn_row.addWidget(cancel_btn)
        btn_row.addStretch()
        btn_row.addWidget(save_btn)
        card_layout.addLayout(btn_row)

        scroll.setWidget(card)
        outer.addWidget(scroll)

    # -- Helpers ----------------------------------------------------------------
    @staticmethod
    def _field_label(text: str) -> QLabel:
        lbl = QLabel(text)
        lbl.setStyleSheet(
            "font-size: 12px; font-weight: 600; color: #6B7A99; background: transparent;"
        )
        return lbl

    @staticmethod
    def _divider() -> QFrame:
        d = QFrame()
        d.setObjectName("HDivider")
        return d

    # -- Chip color overrides --------------------------------------------------------
    def _style_abnormal_chip(self, checked: bool):
        """Chip 'Tidak Normal' tampil merah saat aktif."""
        if checked:
            self.chip_abnormal.setStyleSheet(
                "QPushButton {"
                "  background-color: #E74C3C;"
                "  color: #FFFFFF;"
                "  border: 2px solid #E74C3C;"
                "  border-radius: 10px;"
                "  padding: 8px 20px;"
                "  font-size: 13px;"
                "  font-weight: 700;"
                "}"
                "QPushButton:hover { background-color: #C0392B; border-color: #C0392B; }"
            )
            self.chip_abnormal.setText("\u2713  Tidak Normal")
        else:
            # Kembalikan ke style default (tidak aktif) via _refresh_style
            self.chip_abnormal._refresh_style()

    def _style_normal_chip(self, checked: bool):
        """Pastikan chip 'Normal' selalu biru saat aktif."""
        self.chip_normal._refresh_style()

    # -- Save -------------------------------------------------------------------
    def _save(self):
        nama = self.nama_input.text().strip()
        if not nama:
            self.nama_input.setStyleSheet(
                "border: 2px solid #E74C3C; border-radius: 8px; padding: 9px 12px;"
                " background: #FFF6F6; font-size: 14px;"
            )
            self.nama_input.setPlaceholderText("Nama tidak boleh kosong!")
            self.nama_input.setFocus()
            return

        umur_text = self.umur_input.text().strip()
        if not umur_text:
            self.umur_input.setStyleSheet(
                "border: 2px solid #E74C3C; border-radius: 8px; padding: 9px 12px;"
                " background: #FFF6F6; font-size: 15px; font-weight: 600; color: #1A2340;"
            )
            self.umur_input.setPlaceholderText("Umur wajib diisi!")
            self.umur_input.setFocus()
            return

        umur = int(umur_text)

        # Reset error style
        self.nama_input.setStyleSheet("")
        self.umur_input.setStyleSheet("")

        jk     = self.chip_laki.value() if self._jk_group.checkedId() == 0 else self.chip_perempuan.value()
        status = self.chip_normal.value() if self._status_group.checkedId() == 0 else self.chip_abnormal.value()

        self.respondent_added.emit(
            {
                "nama":          nama,
                "umur":          umur,
                "jenis_kelamin": jk,
                "status":        status,
            }
        )
        self.accept()