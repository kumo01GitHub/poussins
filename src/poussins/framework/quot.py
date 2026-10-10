"""Quot: public-facing quotient-type DSL."""
from __future__ import annotations

from typing import ClassVar

from ..ast import EApp, EConst, Expr
from ..environment.library import QuotDeclaration
from .declared_type import DeclaredType


class Quot(DeclaredType):
    """Immutable wrapper for quotient expressions."""

    TYPE_NAME: ClassVar[str] = QuotDeclaration.QUOT_DECLARATION.declaration.name
    MK_NAME: ClassVar[str] = QuotDeclaration.QUOT_MK_DECLARATION.declaration.name
    LIFT_NAME: ClassVar[str] = (
        QuotDeclaration.QUOT_LIFT_DECLARATION.declaration.name
    )

    @classmethod
    def mk(
        cls,
        carrier_type: Expr,
        relation: Expr,
        value: DeclaredType | Expr,
    ) -> Quot:
        """Construct `Quot.mk value`."""
        value_expr = cls.to_expr(value)
        return cls(
            EApp(
                EApp(EApp(EConst(cls.MK_NAME, ()), carrier_type), relation),
                value_expr,
            )
        )
