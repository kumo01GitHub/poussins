"""Unit declarations."""
from __future__ import annotations

from enum import Enum

from ...ast import EConst
from ..declaration import ConstructorDeclaration, Declaration, InductiveDeclaration
from .sort import Sort


class UnitDeclaration(Enum):
    """Inductive declaration for Unit."""

    UNIT_DECLARATION = InductiveDeclaration(
        name="Unit",
        level_params=(),
        type=Sort.TYPE.sort,
        constructor_names=("Unit.unit",),
    )

    UNIT_UNIT_DECLARATION = ConstructorDeclaration(
        name="Unit.unit",
        level_params=(),
        inductive_name="Unit",
        type=EConst("Unit", ()),
    )

    @property
    def declaration(self) -> Declaration:
        """Return the underlying declaration."""
        return self.value
