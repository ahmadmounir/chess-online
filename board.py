"""
Board — manages the 8×8 grid of piece values and Piece object references.
Coordinate system: grid[x][y] where x = column (0-7), y = row (0-7, top=0).
"""

from __future__ import annotations
from typing import TYPE_CHECKING

from move import Move

if TYPE_CHECKING:
    from pieces.piece import Piece

ROWS = 8
COLS = 8


class Board:
    def __init__(self) -> None:
        # Integer grid: positive = white piece, negative = black, 0 = empty
        self.grid: list[list[int]] = [[0] * ROWS for _ in range(COLS)]
        # Piece object references
        self.pieces: list[list[Piece | None]] = [[None] * ROWS for _ in range(COLS)]

        self.last_move: Move | None = None
        self.last_moves: list[Move] = []
        self.dead_pieces: list[Piece | None] = []   # parallel to last_moves
        self.flipped: bool = False

    # ------------------------------------------------------------------ #
    #  Basic access
    # ------------------------------------------------------------------ #

    def get_piece(self, x: int, y: int) -> "Piece | None":
        """Get piece at coordinate, or None if empty or out of bounds."""
        if 0 <= x < COLS and 0 <= y < ROWS:
            return self.pieces[x][y]
        return None

    def get_grid_value(self, x: int, y: int) -> int:
        """Get piece value at coordinate (positive=white, negative=black)."""
        if 0 <= x < COLS and 0 <= y < ROWS:
            return self.grid[x][y]
        return 0

    def set_grid_value(self, x: int, y: int, v: int) -> None:
        self.grid[x][y] = v

    # ------------------------------------------------------------------ #
    #  Placement & movement
    # ------------------------------------------------------------------ #

    def place_piece(self, x: int, y: int, piece: "Piece | None") -> None:
        """Place or remove piece at coordinate."""
        if piece is not None:
            self.grid[x][y] = piece.board_value
            self.pieces[x][y] = piece
        else:
            self.grid[x][y] = 0
            self.pieces[x][y] = None

    def update_pieces(self, from_x: int, from_y: int,
                       to_x: int, to_y: int,
                       piece: "Piece",
                       all_pieces_ref: list) -> None:
        """Move piece and record captured piece in history."""
        move = Move(from_x, from_y, to_x, to_y)
        self.last_move = move
        self.last_moves.append(move)

        captured = self.pieces[to_x][to_y]
        if captured is not None:
            self.dead_pieces.append(captured)
            if captured in all_pieces_ref:
                all_pieces_ref.remove(captured)
        else:
            self.dead_pieces.append(None)

        piece.x = to_x
        piece.y = to_y

        self.grid[from_x][from_y] = 0
        self.grid[to_x][to_y] = piece.board_value
        self.pieces[from_x][from_y] = None
        self.pieces[to_x][to_y] = piece

    # ------------------------------------------------------------------ #
    #  Clone (used for legal-move verification)
    # ------------------------------------------------------------------ #

    def clone(self) -> "Board":
        """Create a copy of board state for move legality testing."""
        new_board = Board()
        for cx in range(COLS):
            for cy in range(ROWS):
                p = self.pieces[cx][cy]
                if p is not None:
                    cloned = p.clone()
                    cloned.board = new_board
                    new_board.grid[cx][cy] = cloned.board_value
                    new_board.pieces[cx][cy] = cloned
        return new_board

    # ------------------------------------------------------------------ #
    #  Debug
    # ------------------------------------------------------------------ #

    def print_board(self) -> None:
        for y in range(ROWS):
            row = [f"{self.grid[x][y]:3}" for x in range(COLS)]
            print(' '.join(row))
