"""Sorts in the type system, e.g. Prop, Type u, etc."""
from __future__ import annotations

from enum import StrEnum

from .expr import ESort
from .universe import UnivLevel, UnivLevelSucc, UnivLevelZero


class Sort(StrEnum):
    """Sorts in the type system, e.g. Prop, Type u, etc."""

    PROP = "Prop"
    TYPE = "Type"

    @property
    def level(self) -> UnivLevel:
        """Return the universe level corresponding to the sort."""
        match self:
            case Sort.PROP:
                return UnivLevelZero()
            case Sort.TYPE:
                return UnivLevelSucc(UnivLevelZero())

    @property
    def sort(self) -> ESort:
        """Return the ESort corresponding to the sort."""
        return ESort(self.level)
