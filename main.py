"""
Entry point for the Chess client application.
Run:  python main.py
"""

import sys
import os

# Ensure project root is on the path so all imports resolve
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from PyQt6.QtWidgets import QApplication
from PyQt6.QtGui import QIcon

from gui.main_window import MainWindow


def main() -> None:
    app = QApplication(sys.argv)
    app.setApplicationName("Online Chess")
    app.setOrganizationName("FSMVU Networks Lab")

    # Optional: set window icon if available
    icon_path = os.path.join(os.path.dirname(__file__), "resources", "images", "wk.png")
    if os.path.exists(icon_path):
        app.setWindowIcon(QIcon(icon_path))

    window = MainWindow()
    window.show()

    sys.exit(app.exec())


if __name__ == "__main__":
    main()
