from __future__ import annotations
from typing import TYPE_CHECKING

from move import Move
from pieces.piece import Piece

if TYPE_CHECKING:
    from board import Board


class Pawn(Piece):
    def __init__(self, x: int, y: int, is_white: bool,
                 board: "Board", board_value: int) -> None:
        super().__init__(x, y, is_white, board, board_value)
        self.first_move = True
        self.moved_two_squares = False
        self.image_key = "wp" if is_white else "bp"

    # ------------------------------------------------------------------ #

    def can_move(self, x: int, y: int, board: "Board") -> bool:
        direction = -1 if self.is_white else 1   # white moves up (y-1), black down (y+1)

        # --- En-passant check ---
        if 0 < self.x < 7:
            for dx in (1, -1):
                neighbor = board.get_piece(self.x + dx, self.y)
                if (isinstance(neighbor, Pawn) and
                        neighbor.is_white != self.is_white and
                        neighbor.moved_two_squares):
                    if x == self.x + dx and y == self.y + direction:
                        return True

        # Cannot land on own piece
        target = board.get_piece(x, y)
        if target is not None and target.is_white == self.is_white:
            return False

        # Cannot move diagonally unless capturing
        if x != self.x and target is None:
            return False

        # Forward one square
        if x == self.x and y == self.y + direction and target is None:
            return True

        # Forward two squares from start
        if (x == self.x and y == self.y + 2 * direction and
                self.first_move and target is None and
                board.get_piece(x, self.y + direction) is None):
            return True

        # Diagonal capture
        return self._can_capture(x, y)

    def _can_capture(self, x: int, y: int) -> bool:
        direction = -1 if self.is_white else 1
        return (abs(x - self.x) == 1 and y == self.y + direction)

    # ------------------------------------------------------------------ #

    def make_move(self, to_x: int, to_y: int,
                  board: "Board", all_pieces: list) -> bool:
        if not self._is_alive(board):
            return False
        if not self.has_move_to(to_x, to_y):
            return False

        direction = -1 if self.is_white else 1

        # En-passant capture: diagonal move onto empty square
        if to_x != self.x and board.get_piece(to_x, to_y) is None:
            captured = board.get_piece(to_x, self.y)
            if captured is not None and captured in all_pieces:
                all_pieces.remove(captured)
            board.set_grid_value(to_x, self.y, 0)
            board.pieces[to_x][self.y] = None

        # Track double-square move for en-passant
        self.moved_two_squares = (self.first_move and abs(to_y - self.y) == 2)

        # Clear other pawns' en-passant flag
        for p in all_pieces:
            if isinstance(p, Pawn) and p is not self:
                p.moved_two_squares = False

        board.update_pieces(self.x, self.y, to_x, to_y, self, all_pieces)
        self.x = to_x
        self.y = to_y
        self.first_move = False
        return True

    # ------------------------------------------------------------------ #

    def reached_end(self) -> bool:
        return (self.is_white and self.y == 0) or (not self.is_white and self.y == 7)
