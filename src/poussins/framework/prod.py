"""Prod: public-facing direct-product DSL."""
from __future__ import annotations

from typing import ClassVar

from ..ast import EApp, EConst, Expr
from ..environment.library import ProdDeclaration
from .inductive_type import InductiveType


class Prod(InductiveType):
    """Immutable wrapper for direct-product expressions."""

    TYPE_NAME: ClassVar[str] = ProdDeclaration.PROD_DECLARATION.declaration.name
    MK_NAME: ClassVar[str] = ProdDeclaration.PROD_MK_DECLARATION.declaration.name

    @classmethod
    def type(cls, left_type: Expr, right_type: Expr) -> Expr:
        """Return `Prod left_type right_type`."""
        return EApp(EApp(EConst(cls.TYPE_NAME, ()), left_type), right_type)

    @classmethod
    def mk(
        cls,
        left_type: Expr,
        right_type: Expr,
        left: InductiveType | Expr,
        right: InductiveType | Expr,
    ) -> Prod:
        """Construct `Prod.mk left right : Prod left_type right_type`."""
        left_expr = cls.to_expr(left)
        right_expr = cls.to_expr(right)
        return cls(
            EApp(
                EApp(
                    EApp(EApp(EConst(cls.MK_NAME, ()), left_type), right_type),
                    left_expr,
                ),
                right_expr,
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
        """Construct `left = right` over `Prod left_type right_type`."""
        left_expr = cls.to_expr(left)
        right_expr = cls.to_expr(right)
        return EApp(
            EApp(
                EApp(EConst(cls.EQ_NAME, ()), cls.type(left_type, right_type)),
                left_expr,
            ),
            right_expr,
        )
