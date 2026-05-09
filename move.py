"""Move data class — serialisable to/from JSON for network transport."""

from __future__ import annotations
from dataclasses import dataclass, field


@dataclass
class Move:
    from_x: int
    from_y: int
    to_x: int
    to_y: int
    promotion: str | None = field(default=None)   # 'queen' | 'rook' | 'knight' | 'bishop'

    # ------------------------------------------------------------------ #
    #  Serialisation
    # ------------------------------------------------------------------ #

    def to_dict(self) -> dict:
        return {
            "type":      "move",
            "from_x":    self.from_x,
            "from_y":    self.from_y,
            "to_x":      self.to_x,
            "to_y":      self.to_y,
            "promotion": self.promotion,
        }

    @staticmethod
    def from_dict(d: dict) -> "Move":
        return Move(
            from_x=d["from_x"],
            from_y=d["from_y"],
            to_x=d["to_x"],
            to_y=d["to_y"],
            promotion=d.get("promotion"),
        )

    # ------------------------------------------------------------------ #
    #  Helpers
    # ------------------------------------------------------------------ #

    def destination_matches(self, x: int, y: int) -> bool:
        return self.to_x == x and self.to_y == y

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, Move):
            return NotImplemented
        return (self.from_x == other.from_x and self.from_y == other.from_y
                and self.to_x == other.to_x and self.to_y == other.to_y)

    def __hash__(self) -> int:
        return hash((self.from_x, self.from_y, self.to_x, self.to_y))
