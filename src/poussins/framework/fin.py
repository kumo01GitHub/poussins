"""Fin: public-facing finite-index DSL."""
from __future__ import annotations

from typing import ClassVar

from ..ast import EApp, EConst, Expr
from ..environment.library import FinDeclaration
from .inductive_type import InductiveType


class Fin(InductiveType):
    """Immutable wrapper for finite-index expressions."""

    TYPE_NAME: ClassVar[str] = FinDeclaration.FIN_DECLARATION.declaration.name
    ZERO_NAME: ClassVar[str] = FinDeclaration.FIN_ZERO_DECLARATION.declaration.name
    SUCC_NAME: ClassVar[str] = FinDeclaration.FIN_SUCC_DECLARATION.declaration.name
    NAT_SUCC_NAME: ClassVar[str] = "Nat.succ"

    @classmethod
    def type(cls, index: InductiveType | Expr) -> Expr:
        """Return `Fin index`."""
        index_expr = cls.to_expr(index)
        return EApp(EConst(cls.TYPE_NAME, ()), index_expr)

    @classmethod
    def zero(cls, index: InductiveType | Expr) -> Fin:
        """Construct `Fin.zero index : Fin (Nat.succ index)`."""
        index_expr = cls.to_expr(index)
        return cls(EApp(EConst(cls.ZERO_NAME, ()), index_expr))

    @classmethod
    def succ(cls, index: InductiveType | Expr, value: Fin | Expr) -> Fin:
        """Construct `Fin.succ value : Fin (Nat.succ index)`."""
        index_expr = cls.to_expr(index)
        value_expr = cls.to_expr(value)
        return cls(EApp(EApp(EConst(cls.SUCC_NAME, ()), index_expr), value_expr))

    @classmethod
    def succ_index(cls, index: InductiveType | Expr) -> Expr:
        """Return `Nat.succ index`."""
        index_expr = cls.to_expr(index)
        return EApp(EConst(cls.NAT_SUCC_NAME, ()), index_expr)

    @classmethod
    def eq(
        cls,
        index: InductiveType | Expr,
        left: InductiveType | Expr,
        right: InductiveType | Expr,
    ) -> Expr:
        """Construct `left = right` over `Fin index`."""
        left_expr = cls.to_expr(left)
        right_expr = cls.to_expr(right)
        return EApp(
            EApp(EApp(EConst(cls.EQ_NAME, ()), cls.type(index)), left_expr),
            right_expr,
        )
