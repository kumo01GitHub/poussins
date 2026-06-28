"""
"""
from enum import IntEnum


class LogicalSide(IntEnum):

    LEFT = 1
    RIGHT = 2

    @property
    def label(self) -> str:
        return "left" if self == LogicalSide.LEFT else "right"

    @property
    def symbol(self) -> str:
        return "L" if self == LogicalSide.LEFT else "R"
