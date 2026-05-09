from __future__ import annotations
from typing import TYPE_CHECKING

from pieces.piece import Piece

if TYPE_CHECKING:
    from board import Board


class Bishop(Piece):
    def __init__(self, x: int, y: int, is_white: bool,
                 board: "Board", board_value: int) -> None:
        super().__init__(x, y, is_white, board, board_value)
        self.image_key = "wb" if is_white else "bb"

    def can_move(self, x: int, y: int, board: "Board") -> bool:
        target = board.get_piece(x, y)
        if target is not None and target.is_white == self.is_white:
            return False
        if abs(x - self.x) != abs(y - self.y) or x == self.x:
            return False
        return self._path_clear(x, y, board)

    def _path_clear(self, x: int, y: int, board: "Board") -> bool:
        dx = 1 if x > self.x else -1
        dy = 1 if y > self.y else -1
        cx, cy = self.x + dx, self.y + dy
        while (cx, cy) != (x, y):
            if board.get_grid_value(cx, cy) != 0:
                return False
            cx += dx
            cy += dy
        return True
