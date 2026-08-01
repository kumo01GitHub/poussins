from __future__ import annotations
from dataclasses import dataclass


@dataclass(frozen=True)
class UnivLevelZero:
    """The base universe level (0)."""

    def __str__(self) -> str:
        return "0"


@dataclass(frozen=True)
class UnivLevelSucc:
    """The successor of a universe level (n + 1)."""

    pred: UnivLevel

    def __str__(self) -> str:
        return f"({self.pred} + 1)"


@dataclass(frozen=True)
class UnivLevelParam:
    """A parameterized universe level (e.g., a variable)."""

    name: str

    def __str__(self) -> str:
        return self.name


@dataclass(frozen=True)
class UnivLevelMax:
    """The maximum of two universe levels (max(n, m))."""

    left: UnivLevel
    right: UnivLevel

    def __str__(self) -> str:
        return f"max({self.left}, {self.right})"


@dataclass(frozen=True)
class UnivLevelIMax:
    """The imax of two universe levels (imax(n, m))."""

    left: UnivLevel
    right: UnivLevel

    def __str__(self) -> str:
        return f"imax({self.left}, {self.right})"


UnivLevel = UnivLevelZero | UnivLevelSucc | UnivLevelParam | UnivLevelMax | UnivLevelIMax
