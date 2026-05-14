"""
Chess Multiplayer Server - Console Application
Designed to run on AWS EC2. Manages two client connections and relays moves.
"""

import socket
import threading
import json
import sys
import random

PORT = 5000


def send_msg(conn: socket.socket, data: dict) -> None:
    """Send a JSON message terminated by newline."""
    try:
        msg = json.dumps(data) + '\n'
        conn.sendall(msg.encode('utf-8'))
    except OSError:
        pass


def recv_msg(conn: socket.socket) -> dict:
    """Receive a newline-terminated JSON message."""
    buf = b''
    while True:
        chunk = conn.recv(1)
        if not chunk:
            raise ConnectionError("Client disconnected")
        if chunk == b'\n':
            break
        buf += chunk
    return json.loads(buf.decode('utf-8'))


class ChessServer:
    """
    Relay server: waits for two players, then forwards every message
    from player-0 to player-1 and vice-versa.
    """

    def __init__(self):
        self.clients: list[socket.socket | None] = [None, None]
        self.lock = threading.Lock()

    def start(self) -> None:
        server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        server_socket.bind(('0.0.0.0', PORT))
        server_socket.listen(2)
        print(f"[Server] Started on port {PORT} — waiting for 2 players...")

        # Pre-shuffle player IDs for random assignment (0=White, 1=Black)
        player_ids = [0, 1]
        random.shuffle(player_ids)
        id_index = 0
        
        for i in range(2):
            conn, addr = server_socket.accept()
            player_id = player_ids[id_index]
            self.clients[player_id] = conn
            # Tell each client which player they are — send immediately to allow waiting screen
            send_msg(conn, {"type": "player_id", "id": player_id})
            print(f"[Server] Player {i+1} connected from {addr} — assigned as {'White (ID=0)' if player_id == 0 else 'Black (ID=1)'}") 
            id_index += 1

        print("[Server] Both players connected — game starting!")

        # Notify both clients that the game is ready to start
        send_msg(self.clients[0], {"type": "game_ready"})
        send_msg(self.clients[1], {"type": "game_ready"})
        print("[Server] Sent game_ready to both players.")

        t0 = threading.Thread(target=self._relay, args=(0, 1), daemon=True)
        t1 = threading.Thread(target=self._relay, args=(1, 0), daemon=True)
        t0.start()
        t1.start()
        t0.join()
        t1.join()
        print("[Server] Session ended.")

    def _relay(self, src: int, dst: int) -> None:
        """Forward all messages from src player to dst player."""
        try:
            while True:
                data = recv_msg(self.clients[src])
                send_msg(self.clients[dst], data)
                msg_type = data.get("type", "")
                if msg_type == "move":
                    print(f"[Server] Player {src} moved: "
                          f"({data['from_x']},{data['from_y']}) -> ({data['to_x']},{data['to_y']})")
                elif msg_type == "game_over":
                    print(f"[Server] Game over — {data.get('result', '')}")
                elif msg_type == "replay_request":
                    print(f"[Server] Player {src} requested replay.")
                elif msg_type == "replay_accept":
                    print(f"[Server] Player {src} accepted replay.")
        except Exception as e:
            print(f"[Server] Player {src} disconnected: {e}")
            self._notify_win_by_disconnect(dst)
        finally:
            self._close(src)

    def _notify_win_by_disconnect(self, player_idx: int) -> None:
        try:
            if self.clients[player_idx]:
                send_msg(self.clients[player_idx], {"type": "win_by_disconnect"})
        except Exception:
            pass

    def _close(self, idx: int) -> None:
        try:
            if self.clients[idx]:
                self.clients[idx].close()
                self.clients[idx] = None
        except OSError:
            pass


if __name__ == '__main__':
    try:
        ChessServer().start()
    except KeyboardInterrupt:
        print("\n[Server] Shutting down.")
        sys.exit(0)
