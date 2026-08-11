from __future__ import annotations
from enum import Enum

from ...ast import ESort, UnivLevelZero, UnivLevelSucc


class Sort(Enum):
    PROP = ESort(UnivLevelZero())
    TYPE = ESort(UnivLevelSucc(UnivLevelZero()))

    @property
    def sort(self) -> ESort:
        return self.value
