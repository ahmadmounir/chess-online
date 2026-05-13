"""Waiting screen — shown while waiting for the opponent to connect."""

from __future__ import annotations
from PyQt6.QtWidgets import QWidget, QVBoxLayout, QLabel
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QFont, QColor, QPalette


class WaitingScreen(QWidget):
    """
    Displays a simple message while waiting for the opponent to connect.
    No signals or buttons — just a waiting state.
    """

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
        root.setSpacing(30)

        # ── Animation icon / emoji ─────────────────────────────────────
        icon = QLabel("⏳")
        icon.setAlignment(Qt.AlignmentFlag.AlignCenter)
        icon.setFont(QFont("Segoe UI Emoji", 72))
        root.addWidget(icon)

        # ── Main message ───────────────────────────────────────────────
        message = QLabel("Waiting for other player...")
        message.setAlignment(Qt.AlignmentFlag.AlignCenter)
        message.setFont(QFont("Georgia", 24, QFont.Weight.Bold))
        message.setStyleSheet("color: #e2b96f;")
        message.setWordWrap(True)
        root.addWidget(message)

        # ── Subtitle ───────────────────────────────────────────────────
        subtitle = QLabel("Your opponent is connecting...")
        subtitle.setAlignment(Qt.AlignmentFlag.AlignCenter)
        subtitle.setStyleSheet("color: #aaaaaa; font-size: 13px;")
        root.addWidget(subtitle)
