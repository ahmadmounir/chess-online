from __future__ import annotations
from typing import TYPE_CHECKING

from move import Move
from pieces.piece import Piece

if TYPE_CHECKING:
    from board import Board
    from pieces.rook import Rook


class King(Piece):
    def __init__(self, x: int, y: int, is_white: bool,
                 board: "Board", board_value: int) -> None:
        super().__init__(x, y, is_white, board, board_value)
        self.has_moved = False
        self.image_key = "wk" if is_white else "bk"

    def can_move(self, x: int, y: int, board: "Board",
                 enemy_moves: list[Move] | None = None) -> bool:
        dx = abs(self.x - x)
        dy = abs(self.y - y)

        # Normal king move (one square any direction)
        if (dx == 1 and dy == 1) or (dx + dy == 1):
            target = board.get_piece(x, y)
            if target is None or target.is_white != self.is_white:
                return True
            return False

        # Castling
        if self.has_moved:
            return False

        em = enemy_moves or []
        rook = self._get_rook(x, board)
        if rook is None or rook.has_moved:
            return False

        # Determine castling direction
        if x > self.x:  # kingside
            path_cols = range(self.x + 1, rook.x)
            king_target = rook.x - 1
        else:            # queenside
            path_cols = range(rook.x + 1, self.x)
            king_target = rook.x + 2

        if x != king_target:
            return False

        # Path must be empty
        for col in path_cols:
            if board.get_piece(col, self.y) is not None:
                return False

        # King must not pass through or end in check
        cols_to_check = [self.x] + [self.x + (1 if x > self.x else -1), x]
        for col in cols_to_check:
            if any(m.to_x == col and m.to_y == self.y for m in em):
                return False

        return True

    def make_move(self, to_x: int, to_y: int,
                  board: "Board", all_pieces: list,
                  enemy_moves: list[Move] | None = None) -> bool:
        if not self._is_alive(board):
            return False
        if not self.has_move_to(to_x, to_y):
            return False

        rook = self._get_rook(to_x, board)
        board.update_pieces(self.x, self.y, to_x, to_y, self, all_pieces)
        old_x = self.x
        self.x = to_x
        self.y = to_y

        # Move rook if castling
        if rook is not None and not self.has_moved and not rook.has_moved:
            rook.castle_done(to_x, board, all_pieces)

        self.has_moved = True
        return True

    def is_in_check(self, enemy_moves: list[Move]) -> bool:
        return any(m.to_x == self.x and m.to_y == self.y for m in enemy_moves)

    def _get_rook(self, target_x: int, board: "Board") -> "Rook | None":
        from pieces.rook import Rook
        row = 7 if self.is_white else 0
        if target_x >= self.x:   # kingside rook
            p = board.get_piece(7, row)
        else:                     # queenside rook
            p = board.get_piece(0, row)
        return p if isinstance(p, Rook) else None
