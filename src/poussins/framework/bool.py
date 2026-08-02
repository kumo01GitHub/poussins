"""
Bool: public-facing boolean DSL.

This wraps the internal Expr AST for boolean values so data-level booleans can
be manipulated ergonomically from Python.
"""
from __future__ import annotations

from typing import ClassVar

from ..ast import EConst
from ..environment import Environment
from .inductive_type import InductiveType


class Bool(InductiveType):
    """
    Immutable wrapper for boolean expressions.
    """

    TYPE_NAME: ClassVar[str] = Environment.BOOL_DECLARATION.name
    TRUE_NAME: ClassVar[str] = Environment.BOOL_TRUE_DECLARATION.name
    FALSE_NAME: ClassVar[str] = Environment.BOOL_FALSE_DECLARATION.name

    @classmethod
    def true(cls) -> "Bool":
        """Construct the true boolean value."""
        return cls(EConst(cls.TRUE_NAME, levels=()))

    @classmethod
    def false(cls) -> "Bool":
        """Construct the false boolean value."""
        return cls(EConst(cls.FALSE_NAME, levels=()))
