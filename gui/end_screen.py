"""End screen — shown after game over, offers Replay or Quit."""

from __future__ import annotations
from PyQt6.QtWidgets import QWidget, QVBoxLayout, QLabel, QPushButton, QHBoxLayout
from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtGui import QFont, QColor, QPalette


class EndScreen(QWidget):
    """
    Emitted signals:
      replay_requested — user wants to play again
      quit_requested   — user wants to exit the application
    """

    replay_requested = pyqtSignal()
    quit_requested   = pyqtSignal()

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self._build_ui()

    def _build_ui(self) -> None:
        self.setAutoFillBackground(True)
        palette = self.palette()
        palette.setColor(QPalette.ColorRole.Window, QColor("#1a1a2e"))
        self.setPalette(palette)

        root = QVBoxLayout(self)
        root.setAlignment(Qt.AlignmentFlag.AlignCenter)
        root.setSpacing(24)

        # Trophy icon label
        icon = QLabel("🏆")
        icon.setAlignment(Qt.AlignmentFlag.AlignCenter)
        icon.setFont(QFont("Segoe UI Emoji", 56))
        root.addWidget(icon)

        # Result message
        self.result_label = QLabel("Game Over")
        self.result_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.result_label.setFont(QFont("Georgia", 26, QFont.Weight.Bold))
        self.result_label.setStyleSheet("color: #e2b96f;")
        self.result_label.setWordWrap(True)
        root.addWidget(self.result_label)

        # Sub-message
        self.sub_label = QLabel("")
        self.sub_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.sub_label.setStyleSheet("color: #aaaaaa; font-size: 14px;")
        root.addWidget(self.sub_label)

        root.addSpacing(10)

        # Buttons row
        btn_row = QHBoxLayout()
        btn_row.setSpacing(20)

        self.replay_btn = QPushButton("Play Again")
        self.replay_btn.setFixedSize(160, 48)
        self.replay_btn.setFont(QFont("Arial", 13, QFont.Weight.Bold))
        self.replay_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self.replay_btn.setStyleSheet("""
            QPushButton {
                background-color: #e2b96f;
                color: #1a1a2e;
                border-radius: 8px;
                border: none;
            }
            QPushButton:hover  { background-color: #f0cc88; }
            QPushButton:pressed { background-color: #c9a055; }
        """)
        self.replay_btn.clicked.connect(self.replay_requested)
        btn_row.addWidget(self.replay_btn)

        self.quit_btn = QPushButton("Quit")
        self.quit_btn.setFixedSize(160, 48)
        self.quit_btn.setFont(QFont("Arial", 13))
        self.quit_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self.quit_btn.setStyleSheet("""
            QPushButton {
                background-color: #2c2c4e;
                color: #cccccc;
                border-radius: 8px;
                border: 1px solid #555;
            }
            QPushButton:hover  { background-color: #3d3d6b; }
            QPushButton:pressed { background-color: #1e1e36; }
        """)
        self.quit_btn.clicked.connect(self.quit_requested)
        btn_row.addWidget(self.quit_btn)

        root.addLayout(btn_row)

    # ------------------------------------------------------------------ #

    def set_result(self, message: str, sub: str = "") -> None:
        self.result_label.setText(message)
        self.sub_label.setText(sub)

    def show_replay_pending(self) -> None:
        self.replay_btn.setEnabled(False)
        self.replay_btn.setText("Waiting…")

    def reset_replay_button(self) -> None:
        self.replay_btn.setEnabled(True)
        self.replay_btn.setText("Play Again")
