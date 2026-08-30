"""Nat: public-facing natural number DSL.

This wraps the internal Expr AST for natural numbers so proofs can be written
in a more ergonomic way.
"""
from __future__ import annotations

from typing import ClassVar

from ..ast import EApp, EConst, Expr
from ..environment.library import NatDeclaration
from .inductive_type import InductiveType


class Nat(InductiveType):
    """Immutable wrapper for natural number expressions."""

    TYPE_NAME: ClassVar[str] = NatDeclaration.NAT_DECLARATION.declaration.name

    @classmethod
    def zero(cls) -> Nat:
        """Construct zero."""
        return cls(EConst(
            NatDeclaration.NAT_ZERO_DECLARATION.declaration.name, levels=()))

    @classmethod
    def succ(cls, n: Nat | Expr) -> Nat:
        """Construct the successor of a natural number."""
        value = cls.to_expr(n)
        return cls(EApp(EConst(
            NatDeclaration.NAT_SUCC_DECLARATION.declaration.name, levels=()), value))

    @classmethod
    def add(cls, a: Nat | Expr, b: Nat | Expr) -> Nat:
        """Construct Nat.add a b."""
        lhs = cls.to_expr(a)
        rhs = cls.to_expr(b)
        return cls(EApp(EApp(EConst(
            NatDeclaration.NAT_ADD_DECLARATION.declaration.name, levels=()), lhs), rhs))

    def __add__(self, other: Nat | Expr) -> Nat:
        """Allow `a + b` syntax in Python DSL."""
        return self.add(self, other)
