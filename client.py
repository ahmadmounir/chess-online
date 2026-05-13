"""
Network client — connects to the chess relay server using Python sockets.
Runs a background listener thread; communicates with the GUI via Qt signals.
"""

from __future__ import annotations
import socket
import json
import threading

from PyQt6.QtCore import QObject, pyqtSignal

from move import Move


def _send(conn: socket.socket, data: dict) -> None:
    msg = json.dumps(data) + '\n'
    conn.sendall(msg.encode('utf-8'))


def _recv(conn: socket.socket) -> dict:
    buf = b''
    while True:
        chunk = conn.recv(1)
        if not chunk:
            raise ConnectionError("Server closed connection")
        if chunk == b'\n':
            break
        buf += chunk
    return json.loads(buf.decode('utf-8'))


class NetworkClient(QObject):
    """
    Wraps the TCP socket connection to the server.
    Emits Qt signals so the GUI can react safely from the main thread.
    """

    # Emitted when the server sends us an opponent's move
    move_received = pyqtSignal(object)          # payload: Move
    # Emitted when opponent disconnects
    win_by_disconnect = pyqtSignal()
    # Emitted when server forwards a game-over notification
    game_over_received = pyqtSignal(str)        # payload: result message
    # Emitted when opponent requests/accepts replay
    replay_request_received = pyqtSignal()
    replay_accept_received  = pyqtSignal()
    # Emitted when server signals both players are connected and ready
    game_ready = pyqtSignal()
    # Emitted on connection error
    connection_error = pyqtSignal(str)

    def __init__(self, server_ip: str, port: int = 5000) -> None:
        super().__init__()
        self.server_ip = server_ip
        self.port = port
        self.player_id: int = -1        # 0 = White, 1 = Black
        self.is_my_turn: bool = False
        self._socket: socket.socket | None = None
        self._connected: bool = False
        self._game_ready_received: bool = False  # Track if game_ready arrived before signal was connected

    # ------------------------------------------------------------------ #
    #  Connection
    # ------------------------------------------------------------------ #

    def connect(self) -> None:
        """Block until connected and player-ID received. Raises on failure."""
        self._socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self._socket.connect((self.server_ip, self.port))
        self._connected = True

        # First message from server is our player ID
        msg = _recv(self._socket)
        if msg.get("type") != "player_id":
            raise ValueError(f"Unexpected first message: {msg}")
        self.player_id = msg["id"]
        self.is_my_turn = (self.player_id == 0)   # White always starts
        print(f"[Client] Connected as {'White' if self.is_white else 'Black'} (id={self.player_id})")

        # Start background listener
        t = threading.Thread(target=self._listen, daemon=True)
        t.start()

    def disconnect(self) -> None:
        self._connected = False
        try:
            if self._socket:
                self._socket.close()
        except OSError:
            pass

    # ------------------------------------------------------------------ #
    #  Properties
    # ------------------------------------------------------------------ #

    @property
    def is_white(self) -> bool:
        return self.player_id == 0

    # ------------------------------------------------------------------ #
    #  Sending
    # ------------------------------------------------------------------ #

    def send_move(self, move: Move) -> None:
        if not self._connected:
            return
        _send(self._socket, move.to_dict())
        self.is_my_turn = False

    def send_game_over(self, result: str) -> None:
        if not self._connected:
            return
        _send(self._socket, {"type": "game_over", "result": result})

    def send_replay_request(self) -> None:
        if not self._connected:
            return
        _send(self._socket, {"type": "replay_request"})

    def send_replay_accept(self) -> None:
        if not self._connected:
            return
        _send(self._socket, {"type": "replay_accept"})

    # ------------------------------------------------------------------ #
    #  Query
    # ------------------------------------------------------------------ #

    def is_game_ready(self) -> bool:
        """Returns True if game_ready message was received."""
        return self._game_ready_received

    # ------------------------------------------------------------------ #
    #  Background listener
    # ------------------------------------------------------------------ #

    def _listen(self) -> None:
        try:
            while self._connected:
                data = _recv(self._socket)
                self._dispatch(data)
        except Exception as e:
            if self._connected:
                self.connection_error.emit(str(e))

    def _dispatch(self, data: dict) -> None:
        msg_type = data.get("type", "")
        if msg_type == "move":
            move = Move.from_dict(data)
            self.is_my_turn = True
            self.move_received.emit(move)
        elif msg_type == "win_by_disconnect":
            self.win_by_disconnect.emit()
        elif msg_type == "game_over":
            self.game_over_received.emit(data.get("result", "Game over"))
        elif msg_type == "replay_request":
            self.replay_request_received.emit()
        elif msg_type == "replay_accept":
            self.replay_accept_received.emit()
        elif msg_type == "game_ready":
            self._game_ready_received = True
            self.game_ready.emit()
