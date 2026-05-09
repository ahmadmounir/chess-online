"""Start screen — lets the player enter a server IP and connect."""

from __future__ import annotations
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel,
    QLineEdit, QPushButton, QMessageBox, QFrame
)
from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtGui import QFont, QColor, QPalette


class StartScreen(QWidget):
    """
    Emits `connect_requested(ip: str)` when the user clicks Connect.
    The parent window handles the actual socket connection.
    """

    connect_requested = pyqtSignal(str)   # server IP string

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
        root.setSpacing(20)

        # ── Title ──────────────────────────────────────────────────────
        title = QLabel("♟  Online Chess")
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        title.setFont(QFont("Georgia", 36, QFont.Weight.Bold))
        title.setStyleSheet("color: #e2b96f;")
        root.addWidget(title)

        subtitle = QLabel("Multiplayer — powered by Python & PyQt6")
        subtitle.setAlignment(Qt.AlignmentFlag.AlignCenter)
        subtitle.setStyleSheet("color: #aaaaaa; font-size: 13px;")
        root.addWidget(subtitle)

        root.addSpacing(20)

        # ── Card frame ─────────────────────────────────────────────────
        card = QFrame()
        card.setFixedWidth(380)
        card.setStyleSheet("""
            QFrame {
                background-color: #16213e;
                border-radius: 12px;
                border: 1px solid #0f3460;
            }
        """)
        card_layout = QVBoxLayout(card)
        card_layout.setContentsMargins(30, 30, 30, 30)
        card_layout.setSpacing(14)

        # IP label + input
        ip_label = QLabel("Server IP Address")
        ip_label.setStyleSheet("color: #cccccc; font-size: 13px;")
        card_layout.addWidget(ip_label)

        self.ip_input = QLineEdit()
        self.ip_input.setPlaceholderText("e.g. 13.61.26.108 or 127.0.0.1")
        self.ip_input.setText("127.0.0.1")
        self.ip_input.setStyleSheet("""
            QLineEdit {
                background: #0f3460;
                color: white;
                border: 1px solid #e2b96f;
                border-radius: 6px;
                padding: 8px 12px;
                font-size: 14px;
            }
        """)
        card_layout.addWidget(self.ip_input)

        # Port label + input
        port_label = QLabel("Port")
        port_label.setStyleSheet("color: #cccccc; font-size: 13px;")
        card_layout.addWidget(port_label)

        self.port_input = QLineEdit()
        self.port_input.setText("5000")
        self.port_input.setStyleSheet(self.ip_input.styleSheet())
        card_layout.addWidget(self.port_input)

        card_layout.addSpacing(10)

        # Connect button
        self.connect_btn = QPushButton("Connect & Play")
        self.connect_btn.setFixedHeight(44)
        self.connect_btn.setFont(QFont("Arial", 13, QFont.Weight.Bold))
        self.connect_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self.connect_btn.setStyleSheet("""
            QPushButton {
                background-color: #e2b96f;
                color: #1a1a2e;
                border-radius: 8px;
                border: none;
            }
            QPushButton:hover  { background-color: #f0cc88; }
            QPushButton:pressed { background-color: #c9a055; }
        """)
        self.connect_btn.clicked.connect(self._on_connect)
        self.ip_input.returnPressed.connect(self._on_connect)
        self.port_input.returnPressed.connect(self._on_connect)
        card_layout.addWidget(self.connect_btn)

        root.addWidget(card, alignment=Qt.AlignmentFlag.AlignCenter)

        # ── Info footer ────────────────────────────────────────────────
        root.addSpacing(10)
        info = QLabel("White player connects first and moves first.")
        info.setAlignment(Qt.AlignmentFlag.AlignCenter)
        info.setStyleSheet("color: #666666; font-size: 11px;")
        root.addWidget(info)

    # ------------------------------------------------------------------ #

    def _on_connect(self) -> None:
        ip = self.ip_input.text().strip()
        if not ip:
            QMessageBox.warning(self, "Input Error", "Please enter a server IP address.")
            return
        self.connect_btn.setEnabled(False)
        self.connect_btn.setText("Connecting…")
        self.connect_requested.emit(ip)

    def reset_button(self) -> None:
        self.connect_btn.setEnabled(True)
        self.connect_btn.setText("Connect & Play")

    def get_port(self) -> int:
        try:
            return int(self.port_input.text())
        except ValueError:
            return 5000
