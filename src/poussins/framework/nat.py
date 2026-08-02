"""
Nat: public-facing natural number DSL.

This wraps the internal Expr AST for natural numbers so proofs can be written
in a more ergonomic way.
"""
from __future__ import annotations

from dataclasses import dataclass

from ..ast import EApp, EConst, EVar, Expr


@dataclass(frozen=True)
class Nat:
    """
    Immutable wrapper for natural number expressions.
    """

    expr: Expr

    def __init__(self, expr: Expr | str) -> None:
        if isinstance(expr, str):
            expr = EVar(expr)
        object.__setattr__(self, "expr", expr)

    @classmethod
    def zero(cls) -> "Nat":
        """Construct zero."""
        return cls(EConst("Nat.zero", levels=()))

    @classmethod
    def succ(cls, n: "Nat | Expr") -> "Nat":
        """Construct the successor of a natural number."""
        value = n.expr if isinstance(n, Nat) else n
        return cls(EApp(EConst("Nat.succ", levels=()), value))

    @classmethod
    def type(cls) -> Expr:
        """Return the type expression for natural numbers."""
        return EConst("Nat", ())

    @staticmethod
    def to_expr(value: "Nat | Expr") -> Expr:
        """Return the underlying expression."""
        return value.expr if isinstance(value, Nat) else value

    @classmethod
    def eq(cls, left: "Nat | Expr", right: "Nat | Expr") -> Expr:
        """Construct an equality proposition for natural numbers."""
        left_expr = cls.to_expr(left)
        right_expr = cls.to_expr(right)
        return EApp(EApp(EApp(EConst("Eq", ()), EConst("Nat", ())), left_expr), right_expr)

    def __eq__(self, other: object) -> bool:
        if isinstance(other, Nat):
            return self.expr == other.expr
        if isinstance(other, Expr):
            return self.expr == other
        return NotImplemented

    def __hash__(self) -> int:
        return hash(self.expr)

    def __repr__(self) -> str:
        return f"Nat({self.expr!r})"
