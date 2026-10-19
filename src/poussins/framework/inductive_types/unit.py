"""Unit: public-facing unit-value DSL."""
from __future__ import annotations

from dataclasses import dataclass
from typing import ClassVar

from ...ast import EConst
from ...environment.library import UnitDeclaration
from ..inductive import Inductive


@dataclass(frozen=True, init=False)
class Unit(Inductive):
    """Immutable wrapper for unit expressions."""

    TYPE_NAME: ClassVar[str] = UnitDeclaration.UNIT_DECLARATION.declaration.name
    LEVEL_PARAMS: ClassVar[tuple[str, ...]] = (
        UnitDeclaration.UNIT_DECLARATION.declaration.level_params
    )

    @classmethod
    def unit(cls) -> Unit:
        """Construct the unique unit value."""
        return cls(
            EConst(
                name=UnitDeclaration.UNIT_UNIT_DECLARATION.declaration.name,
                levels=cls.levels()
            )
        )
