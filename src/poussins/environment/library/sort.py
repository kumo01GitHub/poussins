"""Standard sorts for propositions and types."""
from __future__ import annotations

from enum import Enum

from ...ast import ESort, UnivLevelSucc, UnivLevelZero


class Sort(Enum):
    """Standard sorts for propositions and types."""

    PROP = ESort(UnivLevelZero())
    TYPE = ESort(UnivLevelSucc(UnivLevelZero()))

    @property
    def sort(self) -> ESort:
        """Return the sort of the sort."""
        return self.value
