"""Abstract base class for all chess pieces."""

from __future__ import annotations
from abc import ABC, abstractmethod
from typing import TYPE_CHECKING
import copy

from move import Move

if TYPE_CHECKING:
    from board import Board

CELL_SIZE = 80   # pixels per square (used by GUI)


class Piece(ABC):
    def __init__(self, x: int, y: int, is_white: bool,
                 board: "Board", board_value: int) -> None:
        self.x = x
        self.y = y
        self.is_white = is_white
        self.board = board
        self.board_value = board_value   # +/- integer identifying piece type
        self.alive = True
        self.moves: list[Move] = []
        self.image_key: str = ""         # e.g. "wp", "bk" — loaded by GUI
        board.place_piece(x, y, self)

    # ------------------------------------------------------------------ #
    #  Move generation
    # ------------------------------------------------------------------ #

    @abstractmethod
    def can_move(self, x: int, y: int, board: "Board") -> bool:
        """Return True if the piece could pseudo-legally move to (x,y)."""

    def fill_pseudo_legal_moves(self, board: "Board") -> None:
        """Populate self.moves with all pseudo-legal destinations."""
        self.moves = []
        for cx in range(8):
            for cy in range(8):
                if self.can_move(cx, cy, board):
                    self.moves.append(Move(self.x, self.y, cx, cy))

    def has_move_to(self, x: int, y: int) -> bool:
        return any(m.destination_matches(x, y) for m in self.moves)

    # ------------------------------------------------------------------ #
    #  Execution
    # ------------------------------------------------------------------ #

    def make_move(self, to_x: int, to_y: int,
                  board: "Board", all_pieces: list) -> bool:
        """Execute a legal move; returns True on success."""
        if not self._is_alive(board):
            return False
        if not self.has_move_to(to_x, to_y):
            return False
        board.update_pieces(self.x, self.y, to_x, to_y, self, all_pieces)
        self.x = to_x
        self.y = to_y
        return True

    def _is_alive(self, board: "Board") -> bool:
        return (self.alive and
                board.get_grid_value(self.x, self.y) == self.board_value and
                board.get_piece(self.x, self.y) is self)

    # ------------------------------------------------------------------ #
    #  Clone
    # ------------------------------------------------------------------ #

    def clone(self) -> "Piece":
        c = copy.copy(self)
        c.moves = list(self.moves)
        return c
