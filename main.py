"""
main.py
Entry point — Sistem Pengukuran Sudut Ankle Bionic Foot Dashboard.

Usage:
    python main.py
"""

import sys
import os
from pathlib import Path

from PySide6.QtWidgets import QApplication
from PySide6.QtGui import QFont, QFontDatabase
from PySide6.QtCore import Qt

from main_window import MainWindow


def load_stylesheet(app: QApplication) -> None:
    """Load the global QSS stylesheet from resources/styles.qss."""
    qss_path = Path(__file__).parent / "resources" / "styles.qss"
    if qss_path.exists():
        with open(qss_path, "r", encoding="utf-8") as f:
            app.setStyleSheet(f.read())
    else:
        print(f"[Warning] Stylesheet not found: {qss_path}")


def main() -> int:
    # ── High-DPI: enabled by default in Qt 6.x, no attributes needed ───────────
    app = QApplication(sys.argv)
    app.setApplicationName("Bionic Foot Dashboard")
    app.setApplicationDisplayName("Sistem Pengukuran Sudut Ankle — Bionic Foot")
    app.setOrganizationName("Bionic Foot Lab")

    # ── Default font ──────────────────────────────────────────────────────────
    default_font = QFont("Segoe UI", 10)
    app.setFont(default_font)

    # ── Load QSS ─────────────────────────────────────────────────────────────
    load_stylesheet(app)

    # ── Launch window ─────────────────────────────────────────────────────────
    window = MainWindow()
    window.show()

    return app.exec()


if __name__ == "__main__":
    sys.exit(main())
