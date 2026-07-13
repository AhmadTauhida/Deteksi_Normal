"""
widgets/metric_card.py
A card widget displaying a large numeric metric (sudut, waktu, jarak).

Revisi: accent bar (garis kiri berwarna) dan warna teks value ber-aksen
dihapus. Kartu sekarang polos & konsisten, memakai style Card standar
(sesuai tema warm neutral). Parameter accent_color tetap diterima untuk
kompatibilitas API lama, tapi tidak lagi mempengaruhi tampilan visual.
"""

from PySide6.QtWidgets import QFrame, QVBoxLayout, QLabel, QHBoxLayout, QWidget
from PySide6.QtCore import Qt


class MetricCard(QFrame):
    """
    Displays a prominent numeric value with label and unit inside a card.

    Args:
        label       (str): Short title, e.g. "Sudut Ankle"
        value       (str): The numeric / text value, e.g. "23.4"
        unit        (str): Unit suffix, e.g. "°"
        accent_color(str): Diterima untuk kompatibilitas, TIDAK dipakai lagi
                           untuk border/warna teks (kartu sudah polos).
    """

    def __init__(
        self,
        label: str = "Metric",
        value: str = "—",
        unit: str = "",
        accent_color: str = "#3E6E63",
        parent=None,
    ):
        super().__init__(parent)
        self.setObjectName("Card")
        self._accent = accent_color  # disimpan untuk kompatibilitas API saja
        self._build_ui(label, value, unit)

    # ------------------------------------------------------------------
    def _build_ui(self, label: str, value: str, unit: str):
        self.setMinimumHeight(110)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 16, 20, 16)
        layout.setSpacing(6)

        # Section label
        self._label_widget = QLabel(label.upper())
        self._label_widget.setObjectName("SectionLabel")
        layout.addWidget(self._label_widget)

        # Value + unit row
        value_row = QHBoxLayout()
        value_row.setSpacing(6)
        value_row.setAlignment(Qt.AlignLeft | Qt.AlignVCenter)

        self._value_widget = QLabel(value)
        self._value_widget.setObjectName("MetricValue")
        value_row.addWidget(self._value_widget)

        self._unit_widget = QLabel(unit)
        self._unit_widget.setObjectName("MetricUnit")
        self._unit_widget.setAlignment(Qt.AlignBottom)
        value_row.addWidget(self._unit_widget)
        value_row.addStretch()

        layout.addLayout(value_row)

    # ------------------------------------------------------------------
    def set_value(self, value: str):
        """Update displayed value."""
        self._value_widget.setText(value)

    def set_unit(self, unit: str):
        self._unit_widget.setText(unit)

    def set_label(self, label: str):
        self._label_widget.setText(label.upper())

    def set_accent(self, color: str):
        """
        Disimpan untuk kompatibilitas API lama. Tidak lagi mengubah
        tampilan visual (kartu sudah didesain polos tanpa aksen warna).
        """
        self._accent = color