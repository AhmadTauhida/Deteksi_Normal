"""
widgets/status_badge.py
Reusable status label for Normal / Tidak Normal.
Revisi: tampilan teks polos berwarna, TANPA kotak/border/background pill.
"""

from PySide6.QtWidgets import QLabel
from PySide6.QtCore import Qt


class StatusBadge(QLabel):
    """
    A QLabel showing colored plain text for status (no box/border).

    Args:
        status (str): "Normal" or "Tidak Normal"
        large  (bool): Use larger variant for the monitoring header.
    """

    def __init__(self, status: str = "Normal", large: bool = False, parent=None):
        super().__init__(parent)
        self._large = large
        self.set_status(status)
        self.setAlignment(Qt.AlignCenter)

    # ------------------------------------------------------------------
    def set_status(self, status: str):
        """Update the label text and visual style."""
        self._status = status
        self.setText(status)

        is_normal = status.strip().lower() == "normal"

        if self._large:
            self.setObjectName("StatusTextNormalLarge" if is_normal else "StatusTextAbnormalLarge")
        else:
            self.setObjectName("StatusTextNormal" if is_normal else "StatusTextAbnormal")

        # Force style refresh after objectName change
        self.style().unpolish(self)
        self.style().polish(self)
        self.update()

    # ------------------------------------------------------------------
    def status(self) -> str:
        return self._status