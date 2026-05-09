"""
Core chess game logic — board state, move validation, turn management,
check/checkmate detection. No GUI or networking code here.
"""

from __future__ import annotations
from typing import Callable
import copy

from board import Board
from move import Move
from pieces.piece import Piece
from pieces.pawn   import Pawn
from pieces.rook   import Rook
from pieces.knight import Knight
from pieces.bishop import Bishop
from pieces.queen  import Queen
from pieces.king   import King

STARTING_FEN = "rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR w KQkq - 0 1"

# Piece board-value table (positive = white)
_VALUES = {'P': 1, 'R': 5, 'N': 3, 'B': 3, 'Q': 8, 'K': 10}
_CLASSES = {'P': Pawn, 'R': Rook, 'N': Knight, 'B': Bishop, 'Q': Queen, 'K': King}


class Game:
    """Full chess game state machine."""

    def __init__(self) -> None:
        # Callbacks wired by the GUI
        self.on_game_over:    Callable[[str], None] | None = None
        self.on_board_changed: Callable[[], None] | None = None

        self.board = Board()
        self.all_pieces:   list[Piece] = []
        self.white_pieces: list[Piece] = []
        self.black_pieces: list[Piece] = []
        self.white_king:   King | None = None
        self.black_king:   King | None = None

        self.white_turn:   bool = True
        self.active_piece: Piece | None = None
        self.game_over:    bool = False
        self.dragging:     bool = False

        self.player_moves: list[Move] = []
        self.enemy_moves:  list[Move] = []

        self._load_fen(STARTING_FEN)
        self._refresh_all()

    # ------------------------------------------------------------------ #
    #  Public API
    # ------------------------------------------------------------------ #

    def reset(self) -> None:
        self.board = Board()
        self.all_pieces.clear()
        self.white_pieces.clear()
        self.black_pieces.clear()
        self.white_king = None
        self.black_king = None
        self.white_turn = True
        self.active_piece = None
        self.game_over = False
        self.dragging = False
        self._load_fen(STARTING_FEN)
        self._refresh_all()

    def select_piece(self, x: int, y: int) -> bool:
        if self.game_over:
            return False
        piece = self.board.get_piece(x, y)
        if piece and piece.is_white == self.white_turn:
            self.active_piece = piece
            return True
        return False

    def try_move(self, to_x: int, to_y: int,
                 promotion_choice: str = "queen") -> bool:
        """
        Attempt to move self.active_piece to (to_x, to_y).
        Returns True on success, False if the move is illegal or no piece selected.
        """
        if self.game_over or self.active_piece is None:
            return False

        piece = self.active_piece
        if not piece.has_move_to(to_x, to_y):
            self.active_piece = None
            self.dragging = False
            return False

        from_x, from_y = piece.x, piece.y

        # Execute the move
        ok = self._execute(piece, to_x, to_y)
        if not ok:
            self.active_piece = None
            self.dragging = False
            return False

        # Pawn promotion
        if isinstance(piece, Pawn) and piece.reached_end():
            self._promote(piece, promotion_choice)

        self._fill_teams()
        self._change_turn()
        self.active_piece = None
        self.dragging = False

        if self.on_board_changed:
            self.on_board_changed()
        return True

    def apply_network_move(self, move: Move) -> bool:
        """Apply an opponent's move received over the network."""
        piece = self.board.get_piece(move.from_x, move.from_y)
        if piece is None:
            return False
        self.active_piece = piece
        return self.try_move(move.to_x, move.to_y,
                             promotion_choice=move.promotion or "queen")

    def is_king_in_check(self) -> King | None:
        """Return current player's king if it is in check, else None."""
        king = self.white_king if self.white_turn else self.black_king
        if king and king.is_in_check(self.enemy_moves):
            return king
        return None

    # ------------------------------------------------------------------ #
    #  Internal move flow
    # ------------------------------------------------------------------ #

    def _execute(self, piece: Piece, to_x: int, to_y: int) -> bool:
        if isinstance(piece, King):
            return piece.make_move(to_x, to_y, self.board, self.all_pieces,
                                   self.enemy_moves)
        return piece.make_move(to_x, to_y, self.board, self.all_pieces)

    def _change_turn(self) -> None:
        self.white_turn = not self.white_turn
        self._refresh_all()
        self._detect_checkmate()

    def _detect_checkmate(self) -> None:
        current = self.white_pieces if self.white_turn else self.black_pieces
        if any(len(p.moves) > 0 for p in current):
            return   # still moves available

        king = self.white_king if self.white_turn else self.black_king
        if king and king.is_in_check(self.enemy_moves):
            winner = "Black" if self.white_turn else "White"
            msg = f"Checkmate! {winner} wins!"
        else:
            msg = "Stalemate! It's a draw."
        self.game_over = True
        if self.on_game_over:
            self.on_game_over(msg)

    # ------------------------------------------------------------------ #
    #  Move generation & legal filtering
    # ------------------------------------------------------------------ #

    def _refresh_all(self) -> None:
        """Regenerate pseudo-legal moves for both sides, then filter legals."""
        opponent = self.black_pieces if self.white_turn else self.white_pieces
        current  = self.white_pieces if self.white_turn else self.black_pieces

        # Step 1 – enemy pseudo-legal (needed for castling check detection)
        self.enemy_moves = self._gen_pseudo(opponent)

        # Step 2 – current player pseudo-legal (king uses enemy_moves)
        for p in current:
            if isinstance(p, King):
                p.fill_pseudo_legal_moves_with_enemy(self.board, self.enemy_moves)
            else:
                p.fill_pseudo_legal_moves(self.board)

        # Step 3 – strip moves that leave own king in check
        king = self.white_king if self.white_turn else self.black_king
        for p in current:
            p.moves = [m for m in p.moves if self._is_legal(p, m, king)]

        self.player_moves = [m for p in current for m in p.moves]

    def _gen_pseudo(self, pieces: list[Piece]) -> list[Move]:
        moves: list[Move] = []
        for p in pieces:
            p.fill_pseudo_legal_moves(self.board)
            moves.extend(p.moves)
        return moves

    def _is_legal(self, piece: Piece, move: Move, king: King | None) -> bool:
        """
        Simulate the move on a cloned board and verify the king is not in check.
        Uses a lightweight clone approach.
        """
        if king is None:
            return True

        # Clone the board
        cb = self.board.clone()
        # All pieces on cloned board
        cloned_all: list[Piece] = [
            cb.pieces[x][y]
            for x in range(8) for y in range(8)
            if cb.pieces[x][y] is not None
        ]

        cp = cb.get_piece(piece.x, piece.y)
        if cp is None:
            return True

        # Generate pseudo-legal moves for cp on cloned board, then apply
        if isinstance(cp, King):
            cp.fill_pseudo_legal_moves(cb)
        else:
            cp.fill_pseudo_legal_moves(cb)

        # Execute the move (ignore return value — clone may differ slightly)
        if isinstance(cp, Pawn):
            cp.make_move(move.to_x, move.to_y, cb, cloned_all)
        else:
            cp.make_move(move.to_x, move.to_y, cb, cloned_all)

        # Locate king on cloned board (it may have moved if cp is King)
        king_x = move.to_x if isinstance(piece, King) else king.x
        king_y = move.to_y if isinstance(piece, King) else king.y
        cloned_king = cb.get_piece(king_x, king_y)
        if cloned_king is None or not isinstance(cloned_king, King):
            # Search for king anywhere
            cloned_king = next(
                (cb.pieces[x][y]
                 for x in range(8) for y in range(8)
                 if isinstance(cb.pieces[x][y], King) and
                 cb.pieces[x][y].is_white == king.is_white),
                None
            )
        if cloned_king is None:
            return True

        # Check if any enemy piece on cloned board attacks the king
        for x in range(8):
            for y in range(8):
                ep = cb.pieces[x][y]
                if ep is not None and ep.is_white != piece.is_white:
                    ep.fill_pseudo_legal_moves(cb)
                    if any(m.to_x == cloned_king.x and m.to_y == cloned_king.y
                           for m in ep.moves):
                        return False
        return True

    # ------------------------------------------------------------------ #
    #  Promotion
    # ------------------------------------------------------------------ #

    def _promote(self, pawn: Pawn, choice: str) -> None:
        x, y, is_white = pawn.x, pawn.y, pawn.is_white
        v = {'queen': 8, 'rook': 5, 'knight': 3, 'bishop': 3}.get(choice, 8)
        board_value = v if is_white else -v

        if pawn in self.all_pieces:
            self.all_pieces.remove(pawn)
        self.board.grid[x][y] = 0
        self.board.pieces[x][y] = None

        cls = {'queen': Queen, 'rook': Rook, 'knight': Knight, 'bishop': Bishop}.get(choice, Queen)
        new_piece = cls(x, y, is_white, self.board, board_value)
        self.all_pieces.append(new_piece)

    # ------------------------------------------------------------------ #
    #  FEN loading
    # ------------------------------------------------------------------ #

    def _load_fen(self, fen: str) -> None:
        parts = fen.split()
        for row_idx, row_str in enumerate(parts[0].split('/')):
            col = 0
            for ch in row_str:
                if ch.isdigit():
                    col += int(ch)
                else:
                    is_white = ch.isupper()
                    letter = ch.upper()
                    board_value = _VALUES.get(letter, 1)
                    if not is_white:
                        board_value = -board_value
                    cls = _CLASSES.get(letter)
                    if cls:
                        p = cls(col, row_idx, is_white, self.board, board_value)
                        self.all_pieces.append(p)
                        if isinstance(p, King):
                            if is_white:
                                self.white_king = p
                            else:
                                self.black_king = p
                    col += 1
        self.white_turn = (len(parts) < 2 or parts[1] == 'w')
        self._fill_teams()

    def _fill_teams(self) -> None:
        self.white_pieces = [p for p in self.all_pieces if p.is_white]
        self.black_pieces = [p for p in self.all_pieces if not p.is_white]


# ── Monkey-patch King to support enemy_moves in castling check ───────────

def _king_fill_with_enemy(self: King, board: Board,
                           enemy_moves: list[Move]) -> None:
    """Custom move generation for King that respects enemy attacks."""
    self.moves = [
        Move(self.x, self.y, cx, cy)
        for cx in range(8) for cy in range(8)
        if self.can_move(cx, cy, board, enemy_moves)
    ]

King.fill_pseudo_legal_moves_with_enemy = _king_fill_with_enemy  # type: ignore
