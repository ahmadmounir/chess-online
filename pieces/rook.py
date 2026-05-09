from __future__ import annotations
from typing import TYPE_CHECKING

from pieces.piece import Piece

if TYPE_CHECKING:
    from board import Board


class Rook(Piece):
    def __init__(self, x: int, y: int, is_white: bool,
                 board: "Board", board_value: int) -> None:
        super().__init__(x, y, is_white, board, board_value)
        self.has_moved = False
        self.just_moved = False          # used by undo logic
        self.image_key = "wr" if is_white else "br"

    def can_move(self, x: int, y: int, board: "Board") -> bool:
        target = board.get_piece(x, y)
        if target is not None and target.is_white == self.is_white:
            return False

        if x == self.x and y < self.y:
            return all(board.get_grid_value(x, i) == 0 for i in range(y + 1, self.y))
        if x == self.x and y > self.y:
            return all(board.get_grid_value(x, i) == 0 for i in range(self.y + 1, y))
        if y == self.y and x > self.x:
            return all(board.get_grid_value(i, y) == 0 for i in range(self.x + 1, x))
        if y == self.y and x < self.x:
            return all(board.get_grid_value(i, y) == 0 for i in range(x + 1, self.x))
        return False

    def make_move(self, to_x: int, to_y: int,
                  board: "Board", all_pieces: list) -> bool:
        if super().make_move(to_x, to_y, board, all_pieces):
            self.just_moved = not self.has_moved
            self.has_moved = True
            return True
        return False

    def castle_done(self, king_x: int, board: "Board", all_pieces: list) -> None:
        """Called by King after castling; moves rook to correct square."""
        if king_x == 6:   # kingside
            new_x = 5
        else:             # queenside
            new_x = 3
        board.update_pieces(self.x, self.y, new_x, self.y, self, all_pieces)
        self.x = new_x
        self.has_moved = True
