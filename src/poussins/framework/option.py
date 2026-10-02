"""Option: public-facing optional-value DSL."""
from __future__ import annotations

from typing import ClassVar

from ..ast import EApp, EConst, Expr
from ..environment.library import OptionDeclaration
from .inductive_type import InductiveType


class Option(InductiveType):
    """Immutable wrapper for optional-value expressions."""

    TYPE_NAME: ClassVar[str] = OptionDeclaration.OPTION_DECLARATION.declaration.name
    NONE_NAME: ClassVar[str] = (
        OptionDeclaration.OPTION_NONE_DECLARATION.declaration.name
    )
    SOME_NAME: ClassVar[str] = (
        OptionDeclaration.OPTION_SOME_DECLARATION.declaration.name
    )

    @classmethod
    def type(cls, elem_type: Expr) -> Expr:
        """Return `Option elem_type`."""
        return EApp(EConst(cls.TYPE_NAME, ()), elem_type)

    @classmethod
    def none(cls, elem_type: Expr) -> Option:
        """Construct `Option.none` for `elem_type`."""
        return cls(EApp(EConst(cls.NONE_NAME, ()), elem_type))

    @classmethod
    def some(cls, elem_type: Expr, value: InductiveType | Expr) -> Option:
        """Construct `Option.some value` for `elem_type`."""
        value_expr = cls.to_expr(value)
        return cls(EApp(EApp(EConst(cls.SOME_NAME, ()), elem_type), value_expr))

    @classmethod
    def eq(
        cls, elem_type: Expr, left: InductiveType | Expr, right: InductiveType | Expr
    ) -> Expr:
        """Construct `left = right` over `Option elem_type`."""
        left_expr = cls.to_expr(left)
        right_expr = cls.to_expr(right)
        return EApp(
            EApp(EApp(EConst(cls.EQ_NAME, ()), cls.type(elem_type)), left_expr),
            right_expr,
        )
