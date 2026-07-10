"""
widgets/metric_card.py
A card widget displaying a large numeric metric (sudut, waktu, jarak).
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
        accent_color(str): Left-border accent color hex string.
    """

    def __init__(
        self,
        label: str = "Metric",
        value: str = "—",
        unit: str = "",
        accent_color: str = "#2D7DD2",
        parent=None,
    ):
        super().__init__(parent)
        self.setObjectName("Card")
        self._accent = accent_color
        self._build_ui(label, value, unit)
        self._apply_accent()

    # ------------------------------------------------------------------
    def _build_ui(self, label: str, value: str, unit: str):
        self.setMinimumHeight(120)

        outer = QHBoxLayout(self)
        outer.setContentsMargins(0, 0, 0, 0)
        outer.setSpacing(0)

        # Colored left accent bar
        self._accent_bar = QFrame()
        self._accent_bar.setFixedWidth(6)
        self._accent_bar.setStyleSheet(
            f"background-color: {self._accent}; border-radius: 3px; border: none;"
        )
        outer.addWidget(self._accent_bar)

        # Content
        content = QWidget()
        layout = QVBoxLayout(content)
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
        self._value_widget.setStyleSheet(f"color: {self._accent};")
        value_row.addWidget(self._value_widget)

        self._unit_widget = QLabel(unit)
        self._unit_widget.setObjectName("MetricUnit")
        self._unit_widget.setAlignment(Qt.AlignBottom)
        value_row.addWidget(self._unit_widget)
        value_row.addStretch()

        layout.addLayout(value_row)
        outer.addWidget(content)

    # ------------------------------------------------------------------
    def _apply_accent(self):
        self._accent_bar.setStyleSheet(
            f"background-color: {self._accent}; border-radius: 3px; border: none;"
        )

    # ------------------------------------------------------------------
    def set_value(self, value: str):
        """Update displayed value."""
        self._value_widget.setText(value)

    def set_unit(self, unit: str):
        self._unit_widget.setText(unit)

    def set_label(self, label: str):
        self._label_widget.setText(label.upper())

    def set_accent(self, color: str):
        self._accent = color
        self._apply_accent()
        self._value_widget.setStyleSheet(f"color: {color};")
