from __future__ import annotations
from typing import TYPE_CHECKING

from pieces.piece import Piece

if TYPE_CHECKING:
    from board import Board

_KNIGHT_DELTAS = [(1,-2),(-1,-2),(-1,2),(1,2),(2,-1),(2,1),(-2,-1),(-2,1)]


class Knight(Piece):
    def __init__(self, x: int, y: int, is_white: bool,
                 board: "Board", board_value: int) -> None:
        super().__init__(x, y, is_white, board, board_value)
        self.image_key = "wn" if is_white else "bn"

    def can_move(self, x: int, y: int, board: "Board") -> bool:
        target = board.get_piece(x, y)
        if target is not None and target.is_white == self.is_white:
            return False
        return (x - self.x, y - self.y) in _KNIGHT_DELTAS
