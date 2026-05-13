"""
Main window — stacked widget controller.
Transitions: StartScreen → GameScreen → EndScreen → StartScreen (replay).
"""

from __future__ import annotations
import threading

from PyQt6.QtWidgets import (
    QMainWindow, QStackedWidget, QWidget, QVBoxLayout,
    QLabel, QMessageBox, QHBoxLayout, QFrame
)
from PyQt6.QtCore import Qt, QMetaObject, Q_ARG, pyqtSlot
from PyQt6.QtGui import QFont, QColor, QPalette

from game import Game
from client import NetworkClient
from move import Move

from gui.start_screen   import StartScreen
from gui.waiting_screen import WaitingScreen
from gui.chess_widget   import ChessWidget
from gui.end_screen     import EndScreen


class GameScreen(QWidget):
    """Wraps ChessWidget with a status bar showing turn info."""

    def __init__(self, game: Game, is_white: bool,
                 parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.setAutoFillBackground(True)
        palette = self.palette()
        palette.setColor(QPalette.ColorRole.Window, QColor("#1a1a2e"))
        self.setPalette(palette)

        root = QVBoxLayout(self)
        root.setContentsMargins(0, 0, 0, 0)
        root.setSpacing(0)

        # ── Status bar ────────────────────────────────────────────────
        status_bar = QFrame()
        status_bar.setFixedHeight(48)
        status_bar.setStyleSheet("background:#0f3460;")
        bar_layout = QHBoxLayout(status_bar)
        bar_layout.setContentsMargins(16, 0, 16, 0)

        self.title_label = QLabel("♟  Online Chess")
        self.title_label.setFont(QFont("Georgia", 14, QFont.Weight.Bold))
        self.title_label.setStyleSheet("color:#e2b96f;")
        bar_layout.addWidget(self.title_label)

        bar_layout.addStretch()

        self.player_label = QLabel(
            f"You are: {'⬜ White' if is_white else '⬛ Black'}"
        )
        self.player_label.setStyleSheet("color:#cccccc; font-size:12px;")
        bar_layout.addWidget(self.player_label)

        bar_layout.addSpacing(20)

        self.turn_label = QLabel()
        self.turn_label.setFont(QFont("Arial", 12, QFont.Weight.Bold))
        self.set_turn(True)   # white always starts
        bar_layout.addWidget(self.turn_label)

        root.addWidget(status_bar)

        # ── Board ─────────────────────────────────────────────────────
        self.chess_widget = ChessWidget(game, is_white, self)
        root.addWidget(self.chess_widget, alignment=Qt.AlignmentFlag.AlignCenter)

    def set_turn(self, white_turn: bool) -> None:
        if white_turn:
            self.turn_label.setText("⬜ White's turn")
            self.turn_label.setStyleSheet("color:#eeeed2;")
        else:
            self.turn_label.setText("⬛ Black's turn")
            self.turn_label.setStyleSheet("color:#769656;")

    def set_waiting(self, waiting: bool) -> None:
        """Dim the turn label when waiting for opponent."""
        if waiting:
            self.turn_label.setStyleSheet("color:#888888;")


class MainWindow(QMainWindow):
    """Top-level window; orchestrates all screens and network events."""

    def __init__(self) -> None:
        super().__init__()
        self.setWindowTitle("Online Chess — PyQt6")
        self.setFixedSize(640, 688)   # 640 board + 48 status bar

        self._stack = QStackedWidget()
        self.setCentralWidget(self._stack)

        self._start_screen:   StartScreen   | None = None
        self._waiting_screen: WaitingScreen | None = None
        self._game_screen:    GameScreen    | None = None
        self._end_screen:     EndScreen     | None = None

        self._game:   Game | None = None
        self._client: NetworkClient | None = None
        self._is_white_player: bool = True

        self._show_start()

    # ------------------------------------------------------------------ #
    #  Screen transitions
    # ------------------------------------------------------------------ #

    def _show_start(self) -> None:
        self.setFixedSize(480, 520)
        if self._start_screen is None:
            self._start_screen = StartScreen()
            self._start_screen.connect_requested.connect(self._on_connect_requested)
            self._stack.addWidget(self._start_screen)
        else:
            self._start_screen.reset_button()
        self._stack.setCurrentWidget(self._start_screen)

    def _show_waiting(self) -> None:
        """Show the waiting screen while we wait for the opponent to connect."""
        self.setFixedSize(480, 520)
        if self._waiting_screen is None:
            self._waiting_screen = WaitingScreen()
            self._stack.addWidget(self._waiting_screen)
        self._stack.setCurrentWidget(self._waiting_screen)

    def _show_game(self) -> None:
        self.setFixedSize(640, 688)
        game = self._game
        is_white = self._is_white_player

        if self._game_screen is not None:
            self._stack.removeWidget(self._game_screen)
            self._game_screen.deleteLater()

        self._game_screen = GameScreen(game, is_white, self)
        cw = self._game_screen.chess_widget
        cw.move_made.connect(self._on_local_move)

        # Wire board-changed → status update
        original_on_changed = game.on_board_changed
        def _update_all():
            if original_on_changed:
                original_on_changed()
            self._game_screen.set_turn(game.white_turn)
            local_turn = (game.white_turn == is_white)
            self._game_screen.set_waiting(not local_turn)
        game.on_board_changed = _update_all

        self._stack.addWidget(self._game_screen)
        self._stack.setCurrentWidget(self._game_screen)
        self._game_screen.set_turn(True)
        self._game_screen.set_waiting(not is_white)  # black waits first

    def _show_end(self, message: str, sub: str = "") -> None:
        self.setFixedSize(480, 400)
        if self._end_screen is None:
            self._end_screen = EndScreen()
            self._end_screen.replay_requested.connect(self._on_replay_requested)
            self._end_screen.quit_requested.connect(self.close)
            self._stack.addWidget(self._end_screen)
        self._end_screen.set_result(message, sub)
        self._end_screen.reset_replay_button()
        self._stack.setCurrentWidget(self._end_screen)

    # ------------------------------------------------------------------ #
    #  Connection flow
    # ------------------------------------------------------------------ #

    def _on_connect_requested(self, ip: str) -> None:
        port = self._start_screen.get_port()

        def _connect_thread():
            try:
                client = NetworkClient(ip, port)
                client.connect()
                # Schedule GUI update on main thread
                QMetaObject.invokeMethod(
                    self, "_on_connected",
                    Qt.ConnectionType.QueuedConnection,
                    Q_ARG(object, client)
                )
            except Exception as e:
                QMetaObject.invokeMethod(
                    self, "_on_connect_failed",
                    Qt.ConnectionType.QueuedConnection,
                    Q_ARG(str, str(e))
                )

        threading.Thread(target=_connect_thread, daemon=True).start()

    @pyqtSlot(object)
    def _on_connected(self, client: NetworkClient) -> None:
        self._client = client
        self._is_white_player = client.is_white

        self._game = Game()
        self._game.on_game_over = self._handle_game_over

        # Connect network signals
        client.move_received.connect(self._on_opponent_move)
        client.win_by_disconnect.connect(self._on_win_by_disconnect)
        client.game_over_received.connect(
            lambda msg: self._handle_game_over(msg))
        client.replay_request_received.connect(self._on_replay_request_received)
        client.replay_accept_received.connect(self._on_replay_accepted)
        client.game_ready.connect(self._on_game_ready)
        client.connection_error.connect(self._on_connection_error)

        self._show_waiting()

        # If game_ready was already received before signal was connected, trigger now
        if self._client.is_game_ready():
            self._on_game_ready()

    @pyqtSlot(str)
    def _on_connect_failed(self, error: str) -> None:
        self._start_screen.reset_button()
        QMessageBox.critical(
            self, "Connection Failed",
            f"Could not connect to server:\n{error}"
        )

    @pyqtSlot()
    def _on_game_ready(self) -> None:
        """Called when server signals both players are connected and ready."""
        self._show_game()

    # ------------------------------------------------------------------ #
    #  Move handling
    # ------------------------------------------------------------------ #

    @pyqtSlot(object)
    def _on_local_move(self, move: Move) -> None:
        """Local player made a move — send it over the network."""
        if self._client:
            self._client.send_move(move)

    @pyqtSlot(object)
    def _on_opponent_move(self, move: Move) -> None:
        """Opponent move received — apply it to the game."""
        if self._game:
            self._game.apply_network_move(move)
            if self._game_screen:
                self._game_screen.chess_widget.update()
                self._game_screen.set_turn(self._game.white_turn)
                local_turn = self._game.white_turn == self._is_white_player
                self._game_screen.set_waiting(not local_turn)

    # ------------------------------------------------------------------ #
    #  Game over
    # ------------------------------------------------------------------ #

    def _handle_game_over(self, message: str) -> None:
        """Called from game logic (may be on any thread) — must be thread-safe."""
        QMetaObject.invokeMethod(
            self, "_show_end_safe",
            Qt.ConnectionType.QueuedConnection,
            Q_ARG(str, message)
        )

    @pyqtSlot(str)
    def _show_end_safe(self, message: str) -> None:
        self._show_end(message, "Press 'Play Again' to start a new game.")

    @pyqtSlot()
    def _on_win_by_disconnect(self) -> None:
        self._show_end("You Win!", "Opponent disconnected.")

    @pyqtSlot(str)
    def _on_connection_error(self, error: str) -> None:
        QMessageBox.warning(self, "Connection Lost",
                            f"Lost connection to server:\n{error}")
        self._show_start()

    # ------------------------------------------------------------------ #
    #  Replay
    # ------------------------------------------------------------------ #

    @pyqtSlot()
    def _on_replay_requested(self) -> None:
        """Local player clicked 'Play Again' — ask opponent."""
        if self._client:
            self._client.send_replay_request()
            if self._end_screen:
                self._end_screen.show_replay_pending()

    @pyqtSlot()
    def _on_replay_request_received(self) -> None:
        """Opponent wants to replay — auto-accept and restart."""
        if self._client:
            self._client.send_replay_accept()
        self._restart_game()

    @pyqtSlot()
    def _on_replay_accepted(self) -> None:
        """Opponent accepted our replay request — restart."""
        self._restart_game()

    def _restart_game(self) -> None:
        if self._game:
            self._game.reset()
            self._show_game()

    # ------------------------------------------------------------------ #

    def closeEvent(self, event) -> None:
        if self._client:
            self._client.disconnect()
        super().closeEvent(event)
