"""
Nat: public-facing natural number DSL.

This wraps the internal Expr AST for natural numbers so proofs can be written
in a more ergonomic way.
"""
from __future__ import annotations

from typing import ClassVar

from ..ast import EApp, EConst, Expr
from ..environment import Environment
from .inductive_type import InductiveType


class Nat(InductiveType):
    """
    Immutable wrapper for natural number expressions.
    """

    TYPE_NAME: ClassVar[str] = Environment.NAT_DECLARATION.name
    ZERO_NAME: ClassVar[str] = Environment.NAT_ZERO_DECLARATION.name
    SUCC_NAME: ClassVar[str] = Environment.NAT_SUCC_DECLARATION.name

    @classmethod
    def zero(cls) -> "Nat":
        """Construct zero."""
        return cls(EConst(cls.ZERO_NAME, levels=()))

    @classmethod
    def succ(cls, n: "Nat | Expr") -> "Nat":
        """Construct the successor of a natural number."""
        value = cls.to_expr(n)
        return cls(EApp(EConst(cls.SUCC_NAME, levels=()), value))
