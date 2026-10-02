"""Sum: public-facing sum-type DSL."""
from __future__ import annotations

from typing import ClassVar

from ..ast import EApp, EConst, Expr
from ..environment.library import SumDeclaration
from .inductive_type import InductiveType


class Sum(InductiveType):
    """Immutable wrapper for sum-type expressions."""

    TYPE_NAME: ClassVar[str] = SumDeclaration.SUM_DECLARATION.declaration.name
    INL_NAME: ClassVar[str] = SumDeclaration.SUM_INL_DECLARATION.declaration.name
    INR_NAME: ClassVar[str] = SumDeclaration.SUM_INR_DECLARATION.declaration.name

    @classmethod
    def type(cls, left_type: Expr, right_type: Expr) -> Expr:
        """Return `Sum left_type right_type`."""
        return EApp(EApp(EConst(cls.TYPE_NAME, ()), left_type), right_type)

    @classmethod
    def inl(cls, left_type: Expr, right_type: Expr, value: InductiveType | Expr) -> Sum:
        """Construct `Sum.inl value : Sum left_type right_type`."""
        value_expr = cls.to_expr(value)
        return cls(
            EApp(
                EApp(EApp(EConst(cls.INL_NAME, ()), left_type), right_type),
                value_expr,
            )
        )

    @classmethod
    def inr(cls, left_type: Expr, right_type: Expr, value: InductiveType | Expr) -> Sum:
        """Construct `Sum.inr value : Sum left_type right_type`."""
        value_expr = cls.to_expr(value)
        return cls(
            EApp(
                EApp(EApp(EConst(cls.INR_NAME, ()), left_type), right_type),
                value_expr,
            )
        )

    @classmethod
    def eq(
        cls,
        left_type: Expr,
        right_type: Expr,
        left: InductiveType | Expr,
        right: InductiveType | Expr,
    ) -> Expr:
        """Construct `left = right` over `Sum left_type right_type`."""
        left_expr = cls.to_expr(left)
        right_expr = cls.to_expr(right)
        return EApp(
            EApp(
                EApp(EConst(cls.EQ_NAME, ()), cls.type(left_type, right_type)),
                left_expr,
            ),
            right_expr,
        )
