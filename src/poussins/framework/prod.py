"""Prod: public-facing direct-product DSL."""
from __future__ import annotations

from typing import ClassVar

from ..ast import EApp, EConst, Expr
from ..environment.library import ProdDeclaration
from .declared_type import DeclaredType


class Prod(DeclaredType):
    """Immutable wrapper for direct-product expressions."""

    TYPE_NAME: ClassVar[str] = ProdDeclaration.PROD_DECLARATION.declaration.name
    MK_NAME: ClassVar[str] = ProdDeclaration.PROD_MK_DECLARATION.declaration.name
    TYPE_ARITY: ClassVar[int] = 2
    EQ_ARITY: ClassVar[int] = 4

    @classmethod
    def type(cls, *args: DeclaredType | Expr) -> Expr:
        """Return `Prod left_type right_type`."""
        if len(args) != cls.TYPE_ARITY:
            raise TypeError(
                f"Prod.type expects {cls.TYPE_ARITY} arguments, got {len(args)}"
            )
        left_type, right_type = args
        return EApp(
            EApp(EConst(cls.TYPE_NAME, ()), cls.to_expr(left_type)),
            cls.to_expr(right_type),
        )

    @classmethod
    def mk(
        cls,
        left_type: Expr,
        right_type: Expr,
        left: DeclaredType | Expr,
        right: DeclaredType | Expr,
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
    def eq(cls, *args: DeclaredType | Expr) -> Expr:
        """Construct `left = right` over `Prod left_type right_type`."""
        if len(args) != cls.EQ_ARITY:
            raise TypeError(
                f"Prod.eq expects {cls.EQ_ARITY} arguments, got {len(args)}"
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
