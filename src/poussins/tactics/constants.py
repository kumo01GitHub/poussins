"""
"""
from enum import IntEnum


class TacticSide(IntEnum):

    LEFT = 1
    RIGHT = 2

    @property
    def label(self) -> str:
        return "left" if self == TacticSide.LEFT else "right"

    @property
    def symbol(self) -> str:
        return "L" if self == TacticSide.LEFT else "R"
