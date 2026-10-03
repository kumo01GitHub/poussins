"""Unit: public-facing unit-value DSL."""
from __future__ import annotations

from typing import ClassVar

from ..ast import EConst
from ..environment.library import UnitDeclaration
from .declared_type import DeclaredType


class Unit(DeclaredType):
    """Immutable wrapper for unit expressions."""

    TYPE_NAME: ClassVar[str] = UnitDeclaration.UNIT_DECLARATION.declaration.name
    UNIT_NAME: ClassVar[str] = UnitDeclaration.UNIT_UNIT_DECLARATION.declaration.name

    @classmethod
    def unit(cls) -> Unit:
        """Construct the unique unit value."""
        return cls(EConst(cls.UNIT_NAME, levels=()))
