"""Fin: public-facing finite-index DSL."""
from __future__ import annotations

from typing import ClassVar

from ..ast import EApp, EConst, Expr
from ..environment.library import FinDeclaration
from .declared_type import DeclaredType


class Fin(DeclaredType):
    """Immutable wrapper for finite-index expressions."""

    TYPE_NAME: ClassVar[str] = FinDeclaration.FIN_DECLARATION.declaration.name
    ZERO_NAME: ClassVar[str] = FinDeclaration.FIN_ZERO_DECLARATION.declaration.name
    SUCC_NAME: ClassVar[str] = FinDeclaration.FIN_SUCC_DECLARATION.declaration.name
    NAT_SUCC_NAME: ClassVar[str] = "Nat.succ"
    TYPE_ARITY: ClassVar[int] = 1
    EQ_ARITY: ClassVar[int] = 3

    @classmethod
    def type(cls, *args: DeclaredType | Expr) -> Expr:
        """Return `Fin index`."""
        if len(args) != cls.TYPE_ARITY:
            raise TypeError(
                f"Fin.type expects {cls.TYPE_ARITY} argument, got {len(args)}"
            )
        (index,) = args
        index_expr = cls.to_expr(index)
        return EApp(EConst(cls.TYPE_NAME, ()), index_expr)

    @classmethod
    def zero(cls, index: DeclaredType | Expr) -> Fin:
        """Construct `Fin.zero index : Fin (Nat.succ index)`."""
        index_expr = cls.to_expr(index)
        return cls(EApp(EConst(cls.ZERO_NAME, ()), index_expr))

    @classmethod
    def succ(cls, index: DeclaredType | Expr, value: Fin | Expr) -> Fin:
        """Construct `Fin.succ value : Fin (Nat.succ index)`."""
        index_expr = cls.to_expr(index)
        value_expr = cls.to_expr(value)
        return cls(EApp(EApp(EConst(cls.SUCC_NAME, ()), index_expr), value_expr))

    @classmethod
    def succ_index(cls, index: DeclaredType | Expr) -> Expr:
        """Return `Nat.succ index`."""
        index_expr = cls.to_expr(index)
        return EApp(EConst(cls.NAT_SUCC_NAME, ()), index_expr)

    @classmethod
    def eq(cls, *args: DeclaredType | Expr) -> Expr:
        """Construct `left = right` over `Fin index`."""
        if len(args) != cls.EQ_ARITY:
            raise TypeError(
                f"Fin.eq expects {cls.EQ_ARITY} arguments, got {len(args)}"
            )
        index, left, right = args
        left_expr = cls.to_expr(left)
        right_expr = cls.to_expr(right)
        return EApp(
            EApp(EApp(EConst(cls.EQ_NAME, ()), cls.type(index)), left_expr),
            right_expr,
        )
