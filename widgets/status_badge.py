"""
widgets/status_badge.py
Reusable colored badge for Normal / Tidak Normal status.
"""

from PySide6.QtWidgets import QLabel
from PySide6.QtCore import Qt


class StatusBadge(QLabel):
    """
    A QLabel styled as a colored pill badge.

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
        """Update the badge text and visual style."""
        self._status = status
        self.setText(status)

        is_normal = status.strip().lower() == "normal"

        if self._large:
            self.setObjectName("BadgeNormalLarge" if is_normal else "BadgeAbnormalLarge")
            font_size = "13px"
            padding = "6px 16px"
        else:
            self.setObjectName("BadgeNormal" if is_normal else "BadgeAbnormal")
            font_size = "11px"
            padding = "4px 12px"

        # Inline styling: TIDAK bergantung pada QSS global/eksternal.
        # Kalau tema aplikasi berubah atau stylesheet global belum/tidak
        # dimuat, badge ini tetap terlihat karena warnanya sudah "dibakar"
        # langsung ke widget (setStyleSheet widget-level selalu punya
        # prioritas lebih tinggi daripada QSS di level QApplication).
        if is_normal:
            bg_color = "#D1FAE5"
            text_color = "#059669"
        else:
            bg_color = "#FEE2E2"
            text_color = "#DC2626"

        self.setStyleSheet(
            f"""
            QLabel {{
                background-color: {bg_color};
                color: {text_color};
                border-radius: 10px;
                padding: {padding};
                font-size: {font_size};
                font-weight: 600;
            }}
            """
        )

        self.update()

    # ------------------------------------------------------------------
    def status(self) -> str:
        return self._status