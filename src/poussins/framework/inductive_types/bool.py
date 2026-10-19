"""Bool: public-facing boolean DSL.

This wraps the internal Expr AST for boolean values so data-level booleans can
be manipulated ergonomically from Python.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import ClassVar

from ...ast import EConst
from ...environment.library import BoolDeclaration
from ..inductive import Inductive


@dataclass(frozen=True, init=False)
class Bool(Inductive):
    """Immutable wrapper for boolean expressions."""

    TYPE_NAME: ClassVar[str] = (
        BoolDeclaration.BOOL_DECLARATION.declaration.name
    )
    LEVEL_PARAMS: ClassVar[tuple[str, ...]] = (
        BoolDeclaration.BOOL_DECLARATION.declaration.level_params
    )

    @classmethod
    def true(cls) -> Bool:
        """Construct the true boolean value."""
        return cls(
            EConst(
                name=BoolDeclaration.BOOL_TRUE_DECLARATION.declaration.name,
                levels=cls.levels()
            )
        )

    @classmethod
    def false(cls) -> Bool:
        """Construct the false boolean value."""
        return cls(
            EConst(
                name=BoolDeclaration.BOOL_FALSE_DECLARATION.declaration.name,
                levels=cls.levels()
            )
        )
