"""
Chess board widget — handles painting and mouse input for the chess game.
Communicates with Game (logic) and NetworkClient (network) via method calls
and Qt signals.
"""

from __future__ import annotations
import os
import sys

from PyQt6.QtWidgets import QWidget, QDialog, QVBoxLayout, QPushButton, QLabel
from PyQt6.QtCore import Qt, QRect, QPoint, pyqtSignal
from PyQt6.QtGui import (
    QPainter, QColor, QPixmap, QFont, QPen, QBrush
)

from game import Game
from move import Move
from pieces.piece import Piece
from pieces.pawn   import Pawn
from pieces.king   import King

CELL = 80                          # pixels per square
BOARD_SIZE = CELL * 8             # 640
LIGHT = QColor("#eeeed2")
DARK  = QColor("#769656")
HIGHLIGHT_SEL    = QColor(255, 255,   0, 100)   # selected piece
HIGHLIGHT_MOVE   = QColor( 50,  50, 200,  80)   # possible move dot
HIGHLIGHT_CAPTURE= QColor(220,  80,  40, 130)   # capture move
HIGHLIGHT_CHECK  = QColor(220,  30,  30, 160)   # king in check
LAST_MOVE_COLOR  = QColor(255, 255,   0,  60)   # last move tint

# Piece image keys
_IMAGE_KEYS = ["wp","bp","wr","br","wn","bn","wb","bb","wq","bq","wk","bk"]


def _images_dir() -> str:
    base = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    return os.path.join(base, "resources", "images")


class ChessWidget(QWidget):
    """Renders the chess board and handles player interaction."""

    # Emitted after the local player completes a move (to send over network)
    move_made = pyqtSignal(object)   # payload: Move
    # Emitted when promotion is needed (before move is fully committed)
    promotion_needed = pyqtSignal()

    def __init__(self, game: Game, is_white_player: bool,
                 parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.game = game
        self.is_white_player = is_white_player
        self.flipped = not is_white_player       # Black sees flipped board

        self.setFixedSize(BOARD_SIZE, BOARD_SIZE)
        self.setMouseTracking(True)

        self._images: dict[str, QPixmap] = {}
        self._load_images()

        self._drag_pos: QPoint | None = None     # current mouse position while dragging
        self._pending_promotion: tuple[int, int] | None = None  # (to_x, to_y)

        # Wire game callbacks
        self.game.on_board_changed = self.update

    # ------------------------------------------------------------------ #
    #  Image loading
    # ------------------------------------------------------------------ #

    def _load_images(self) -> None:
        img_dir = _images_dir()
        for key in _IMAGE_KEYS:
            path = os.path.join(img_dir, f"{key}.png")
            if os.path.exists(path):
                self._images[key] = QPixmap(path).scaled(
                    CELL, CELL,
                    Qt.AspectRatioMode.KeepAspectRatio,
                    Qt.TransformationMode.SmoothTransformation
                )

    # ------------------------------------------------------------------ #
    #  Coordinate helpers
    # ------------------------------------------------------------------ #

    def _to_board(self, px: int, py: int) -> tuple[int, int]:
        """Convert pixel (px,py) → board (col,row)."""
        col = int(px // CELL)
        row = int(py // CELL)
        if self.flipped:
            col = 7 - col
            row = 7 - row
        return col, row

    def _to_pixel(self, bx: int, by: int) -> tuple[int, int]:
        """Convert board (col,row) → pixel top-left."""
        if self.flipped:
            bx = 7 - bx
            by = 7 - by
        return bx * CELL, by * CELL

    # ------------------------------------------------------------------ #
    #  Painting
    # ------------------------------------------------------------------ #

    def paintEvent(self, _) -> None:
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)

        self._draw_board(painter)
        self._draw_last_move(painter)
        self._draw_check(painter)
        self._draw_highlights(painter)
        self._draw_pieces(painter)
        self._draw_drag(painter)
        self._draw_coordinates(painter)

    def _draw_board(self, p: QPainter) -> None:
        for col in range(8):
            for row in range(8):
                color = LIGHT if (col + row) % 2 == 0 else DARK
                px, py = self._to_pixel(col, row)
                p.fillRect(px, py, CELL, CELL, color)

    def _draw_last_move(self, p: QPainter) -> None:
        lm = self.game.board.last_move
        if lm is None:
            return
        for bx, by in [(lm.from_x, lm.from_y), (lm.to_x, lm.to_y)]:
            px, py = self._to_pixel(bx, by)
            p.fillRect(px, py, CELL, CELL, LAST_MOVE_COLOR)

    def _draw_check(self, p: QPainter) -> None:
        king = self.game.is_king_in_check()
        if king:
            px, py = self._to_pixel(king.x, king.y)
            p.fillRect(px, py, CELL, CELL, HIGHLIGHT_CHECK)

    def _draw_highlights(self, p: QPainter) -> None:
        ap = self.game.active_piece
        if ap is None:
            return

        # Selected piece square
        px, py = self._to_pixel(ap.x, ap.y)
        p.fillRect(px, py, CELL, CELL, HIGHLIGHT_SEL)

        # Possible move indicators
        for move in ap.moves:
            mpx, mpy = self._to_pixel(move.to_x, move.to_y)
            target = self.game.board.get_piece(move.to_x, move.to_y)
            if target is not None and target.is_white != ap.is_white:
                # Capture — orange ring
                pen = QPen(HIGHLIGHT_CAPTURE, 5)
                p.setPen(pen)
                p.setBrush(Qt.BrushStyle.NoBrush)
                p.drawEllipse(mpx + 4, mpy + 4, CELL - 8, CELL - 8)
            else:
                # Quiet move — small dot
                p.setBrush(QBrush(HIGHLIGHT_MOVE))
                p.setPen(Qt.PenStyle.NoPen)
                dot_size = CELL // 3
                offset = (CELL - dot_size) // 2
                p.drawEllipse(mpx + offset, mpy + offset, dot_size, dot_size)

    def _draw_pieces(self, p: QPainter) -> None:
        for col in range(8):
            for row in range(8):
                piece = self.game.board.get_piece(col, row)
                if piece is None:
                    continue
                # Don't draw dragged piece in its original square
                if (self.game.active_piece is piece and
                        self.game.dragging and
                        self._drag_pos is not None):
                    continue
                px, py = self._to_pixel(col, row)
                img = self._images.get(piece.image_key)
                if img:
                    p.drawPixmap(px, py, img)

    def _draw_drag(self, p: QPainter) -> None:
        if (self.game.active_piece and
                self.game.dragging and
                self._drag_pos is not None):
            img = self._images.get(self.game.active_piece.image_key)
            if img:
                px = self._drag_pos.x() - CELL // 2
                py = self._drag_pos.y() - CELL // 2
                p.drawPixmap(px, py, img)

    def _draw_coordinates(self, p: QPainter) -> None:
        """Draw rank (1-8) and file (a-h) labels along edges."""
        font = QFont("Arial", 9, QFont.Weight.Bold)
        p.setFont(font)
        files = "abcdefgh"
        ranks = "87654321"
        if self.flipped:
            files = files[::-1]
            ranks = ranks[::-1]

        for i in range(8):
            # File letters at bottom
            color = DARK if i % 2 == 0 else LIGHT
            p.setPen(color)
            p.drawText(QRect(i * CELL + 2, 7 * CELL + 60, CELL, 20),
                       Qt.AlignmentFlag.AlignLeft, files[i])
            # Rank numbers at left
            color = LIGHT if i % 2 == 0 else DARK
            p.setPen(color)
            p.drawText(QRect(2, i * CELL + 2, 20, 20),
                       Qt.AlignmentFlag.AlignLeft, ranks[i])

    # ------------------------------------------------------------------ #
    #  Mouse events
    # ------------------------------------------------------------------ #

    def mousePressEvent(self, event) -> None:
        if event.button() != Qt.MouseButton.LeftButton:
            return
        if self.game.white_turn != self.is_white_player:
            return
        col, row = self._to_board(event.position().x(), event.position().y())

        if self.game.game_over:
            return

        ap = self.game.active_piece
        if ap is not None:
            # Clicking a possible destination → move
            if ap.has_move_to(col, row):
                self._attempt_move(col, row)
                return
            # Clicking own piece → reselect
            piece = self.game.board.get_piece(col, row)
            if piece and piece.is_white == self.game.white_turn:
                self.game.active_piece = None
                self.game.select_piece(col, row)
                self.update()
                return
            # Click elsewhere → deselect
            self.game.active_piece = None
            self.update()
        else:
            self.game.select_piece(col, row)
            self.update()

    def mouseMoveEvent(self, event) -> None:
        if self.game.active_piece and event.buttons() & Qt.MouseButton.LeftButton:
            self.game.dragging = True
            self._drag_pos = event.position().toPoint()
            self.update()

    def mouseReleaseEvent(self, event) -> None:
        if event.button() != Qt.MouseButton.LeftButton:
            return
        if self.game.white_turn != self.is_white_player:
            return
        if self.game.active_piece and self.game.dragging:
            col, row = self._to_board(event.position().x(), event.position().y())
            self._attempt_move(col, row)
        self._drag_pos = None
        self.game.dragging = False
        self.update()

    # ------------------------------------------------------------------ #
    #  Move execution
    # ------------------------------------------------------------------ #

    def _attempt_move(self, to_x: int, to_y: int) -> None:
        ap = self.game.active_piece
        if ap is None:
            return

        from_x, from_y = ap.x, ap.y
        promotion_choice = "queen"

        # Check if pawn promotion is required
        if isinstance(ap, Pawn):
            end_row = 0 if ap.is_white else 7
            if to_y == end_row:
                promotion_choice = self._ask_promotion(ap.is_white)

        self._drag_pos = None
        self.game.dragging = False

        success = self.game.try_move(to_x, to_y, promotion_choice)
        if success:
            move = Move(from_x, from_y, to_x, to_y,
                        promotion=promotion_choice if isinstance(ap, Pawn) else None)
            self.move_made.emit(move)
        self.update()

    # ------------------------------------------------------------------ #
    #  Promotion dialog
    # ------------------------------------------------------------------ #

    def _ask_promotion(self, is_white: bool) -> str:
        dlg = PromotionDialog(is_white, self._images, self)
        dlg.exec()
        return dlg.choice


class PromotionDialog(QDialog):
    """Modal dialog for pawn promotion piece selection."""

    def __init__(self, is_white: bool, images: dict[str, QPixmap],
                 parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.choice = "queen"
        self.setWindowTitle("Pawn Promotion")
        self.setModal(True)
        self.setWindowFlags(
            Qt.WindowType.Dialog | Qt.WindowType.FramelessWindowHint
        )
        self.setStyleSheet("background:#16213e; border-radius:10px;")

        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 20, 20, 20)

        label = QLabel("Promote pawn to:")
        label.setStyleSheet("color:white; font-size:14px; font-weight:bold;")
        label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(label)

        prefix = "w" if is_white else "b"
        options = [("queen", "Queen"), ("rook", "Rook"),
                   ("knight", "Knight"), ("bishop", "Bishop")]

        for key, name in options:
            btn = QPushButton()
            btn.setFixedHeight(60)
            img = images.get(prefix + key[0])
            if img:
                btn.setIcon(img.toImage().__class__(img.toImage()))
                from PyQt6.QtGui import QIcon
                btn.setIcon(QIcon(img))
                btn.setIconSize(img.size())
            btn.setText(f"  {name}")
            btn.setStyleSheet("""
                QPushButton {
                    background:#0f3460; color:white; border-radius:6px;
                    font-size:13px; text-align:left; padding-left:10px;
                }
                QPushButton:hover { background:#1a5276; }
            """)
            btn.clicked.connect(lambda _, k=key: self._choose(k))
            layout.addWidget(btn)

    def _choose(self, key: str) -> None:
        self.choice = key
        self.accept()
