# Chess Online — Python

A two-player online chess game built with **Python** and **PyQt6**. A lightweight relay server connects two clients over the network; all chess rules (castling, en passant, promotion, check, checkmate, stalemate) are enforced client-side.

---

## Requirements

- Python 3.10+
- PyQt6

Install dependencies:

```bash
pip install -r requirements.txt
```

---

## Playing Locally (Same Machine)

Both players run on the same computer using `localhost`.

**Step 1 — Start the server**

```bash
python server.py
```

The server listens on port `5000` and waits for two players to connect.

**Step 2 — Open two client windows**

In two separate terminals, run:

```bash
python main.py
```

**Step 3 — Connect both clients**

In each client window, the start screen will prompt for an IP and port:

- **IP:** `127.0.0.1`
- **Port:** `5000`

Click **Connect & Play** in both windows. The first to connect plays as **White**; the second plays as **Black**.

---

## Playing Online (Over the Internet)

One player hosts the server (e.g. on a cloud VM or a machine with a public IP), and both players connect to it.

### Host Setup

**Step 1 — Run the server on the host machine**

```bash
python server.py
```

Make sure **port 5000** is open in your firewall / security group rules (TCP inbound).

> On AWS EC2, add an inbound rule: `Custom TCP | Port 5000 | Source 0.0.0.0/0`

**Step 2 — Share your public IP**

Find your public IP:

- Linux/macOS: `curl ifconfig.me`
- Windows: `curl ifconfig.me` in PowerShell, or check your router settings
- AWS EC2: use the **Public IPv4** shown in the EC2 console

### Both Players

**Step 1 — Run the client**

```bash
python main.py
```

**Step 2 — Connect to the host**

On the start screen enter:

- **IP:** `<host's public IP>`
- **Port:** `5000`

Click **Connect & Play**. Once both players connect, the game starts automatically.

---

## How to Play

| Action | How |
|--------|-----|
| Select a piece | Click it |
| Move | Click the destination square (highlighted dots show legal moves) |
| Capture | Click the highlighted capture ring |
| Promote a pawn | A dialog appears when a pawn reaches the last rank |
| Rematch | Both players click **Play Again** on the end screen |
| Quit | Close the window or click **Quit** on the end screen |

- The board flips automatically for the Black player.
- If your opponent disconnects mid-game you win by default.

---

## Project Structure

```
Chess Online Python/
├── main.py          # Client entry point
├── server.py        # Relay server
├── client.py        # Network client (Qt signals)
├── game.py          # Chess rules & move validation
├── board.py         # Board state
├── move.py          # Move data class
├── requirements.txt
├── gui/
│   ├── main_window.py   # Screen orchestration
│   ├── start_screen.py  # Connection dialog
│   ├── chess_widget.py  # Board rendering & input
│   └── end_screen.py    # Game over & replay
├── pieces/
│   ├── pawn.py, rook.py, knight.py, bishop.py, queen.py, king.py
└── resources/images/    # Chess piece PNGs
```
