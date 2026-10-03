"""Sigma: public-facing dependent-pair DSL."""
from __future__ import annotations

from typing import ClassVar

from ..ast import EApp, EConst, Expr
from ..environment.library import SigmaDeclaration
from .declared_type import DeclaredType


class Sigma(DeclaredType):
    """Immutable wrapper for dependent-pair expressions."""

    TYPE_NAME: ClassVar[str] = SigmaDeclaration.SIGMA_DECLARATION.declaration.name
    MK_NAME: ClassVar[str] = SigmaDeclaration.SIGMA_MK_DECLARATION.declaration.name
    TYPE_ARITY: ClassVar[int] = 2
    EQ_ARITY: ClassVar[int] = 4

    @classmethod
    def type(cls, *args: DeclaredType | Expr) -> Expr:
        """Return `Sigma value_type family`."""
        if len(args) != cls.TYPE_ARITY:
            raise TypeError(
                f"Sigma.type expects {cls.TYPE_ARITY} arguments, got {len(args)}"
            )
        value_type, family = args
        return EApp(
            EApp(EConst(cls.TYPE_NAME, ()), cls.to_expr(value_type)),
            cls.to_expr(family),
        )

    @classmethod
    def mk(
        cls,
        value_type: Expr,
        family: Expr,
        left: DeclaredType | Expr,
        right: DeclaredType | Expr,
    ) -> Sigma:
        """Construct `Sigma.mk left right : Sigma value_type family`."""
        left_expr = cls.to_expr(left)
        right_expr = cls.to_expr(right)
        return cls(
            EApp(
                EApp(
                    EApp(EApp(EConst(cls.MK_NAME, ()), value_type), family),
                    left_expr,
                ),
                right_expr,
            )
        )

    @classmethod
    def eq(cls, *args: DeclaredType | Expr) -> Expr:
        """Construct `left = right` over `Sigma value_type family`."""
        if len(args) != cls.EQ_ARITY:
            raise TypeError(
                f"Sigma.eq expects {cls.EQ_ARITY} arguments, got {len(args)}"
            )
        value_type, family, left, right = args
        left_expr = cls.to_expr(left)
        right_expr = cls.to_expr(right)
        return EApp(
            EApp(
                EApp(EConst(cls.EQ_NAME, ()), cls.type(value_type, family)),
                left_expr,
            ),
            right_expr,
        )
