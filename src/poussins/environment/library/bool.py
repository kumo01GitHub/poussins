from __future__ import annotations
from enum import Enum

from .sort import Sort
from ..declaration import ConstructorDeclaration, Declaration, InductiveDeclaration
from ...ast.expr import EConst


class BoolDeclaration(Enum):
    """
    Inductive declaration for booleans.
    """

    """Bool inductive declaration for booleans."""
    BOOL_DECLARATION = InductiveDeclaration(
        name="Bool",
        level_params=(),
        type=Sort.TYPE.sort,
        constructor_names=("Bool.true", "Bool.false"),
    )
    """Bool.true constructor declaration for booleans."""
    BOOL_TRUE_DECLARATION = ConstructorDeclaration(
        name="Bool.true",
        level_params=(),
        inductive_name="Bool",
        type=EConst("Bool", ()),
    )
    """Bool.false constructor declaration for booleans."""
    BOOL_FALSE_DECLARATION = ConstructorDeclaration(
        name="Bool.false",
        level_params=(),
        inductive_name="Bool",
        type=EConst("Bool", ()),
    )

    @property
    def declaration(self) -> Declaration:
        """Return the underlying declaration."""
        return self.value
