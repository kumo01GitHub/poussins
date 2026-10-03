"""Sum: public-facing sum-type DSL."""
from __future__ import annotations

from typing import ClassVar

from ..ast import EApp, EConst, Expr
from ..environment.library import SumDeclaration
from .declared_type import DeclaredType


class Sum(DeclaredType):
    """Immutable wrapper for sum-type expressions."""

    TYPE_NAME: ClassVar[str] = SumDeclaration.SUM_DECLARATION.declaration.name
    INL_NAME: ClassVar[str] = SumDeclaration.SUM_INL_DECLARATION.declaration.name
    INR_NAME: ClassVar[str] = SumDeclaration.SUM_INR_DECLARATION.declaration.name
    TYPE_ARITY: ClassVar[int] = 2
    EQ_ARITY: ClassVar[int] = 4

    @classmethod
    def type(cls, *args: DeclaredType | Expr) -> Expr:
        """Return `Sum left_type right_type`."""
        if len(args) != cls.TYPE_ARITY:
            raise TypeError(
                f"Sum.type expects {cls.TYPE_ARITY} arguments, got {len(args)}"
            )
        left_type, right_type = args
        return EApp(
            EApp(EConst(cls.TYPE_NAME, ()), cls.to_expr(left_type)),
            cls.to_expr(right_type),
        )

    @classmethod
    def inl(cls, left_type: Expr, right_type: Expr, value: DeclaredType | Expr) -> Sum:
        """Construct `Sum.inl value : Sum left_type right_type`."""
        value_expr = cls.to_expr(value)
        return cls(
            EApp(
                EApp(EApp(EConst(cls.INL_NAME, ()), left_type), right_type),
                value_expr,
            )
        )

    @classmethod
    def inr(cls, left_type: Expr, right_type: Expr, value: DeclaredType | Expr) -> Sum:
        """Construct `Sum.inr value : Sum left_type right_type`."""
        value_expr = cls.to_expr(value)
        return cls(
            EApp(
                EApp(EApp(EConst(cls.INR_NAME, ()), left_type), right_type),
                value_expr,
            )
        )

    @classmethod
    def eq(cls, *args: DeclaredType | Expr) -> Expr:
        """Construct `left = right` over `Sum left_type right_type`."""
        if len(args) != cls.EQ_ARITY:
            raise TypeError(
                f"Sum.eq expects {cls.EQ_ARITY} arguments, got {len(args)}"
            )
        left_type, right_type, left, right = args
        left_expr = cls.to_expr(left)
        right_expr = cls.to_expr(right)
        return EApp(
            EApp(
                EApp(EConst(cls.EQ_NAME, ()), cls.type(left_type, right_type)),
                left_expr,
            ),
            right_expr,
        )
