"""Option: public-facing optional-value DSL."""
from __future__ import annotations

from typing import ClassVar

from ..ast import EApp, EConst, Expr
from ..environment.library import OptionDeclaration
from .declared_type import DeclaredType


class Option(DeclaredType):
    """Immutable wrapper for optional-value expressions."""

    TYPE_NAME: ClassVar[str] = OptionDeclaration.OPTION_DECLARATION.declaration.name
    NONE_NAME: ClassVar[str] = (
        OptionDeclaration.OPTION_NONE_DECLARATION.declaration.name
    )
    SOME_NAME: ClassVar[str] = (
        OptionDeclaration.OPTION_SOME_DECLARATION.declaration.name
    )
    TYPE_ARITY: ClassVar[int] = 1
    EQ_ARITY: ClassVar[int] = 3

    @classmethod
    def type(cls, *args: DeclaredType | Expr) -> Expr:
        """Return `Option elem_type`."""
        if len(args) != cls.TYPE_ARITY:
            raise TypeError(
                f"Option.type expects {cls.TYPE_ARITY} argument, got {len(args)}"
            )
        (elem_type,) = args
        return EApp(EConst(cls.TYPE_NAME, ()), cls.to_expr(elem_type))

    @classmethod
    def none(cls, elem_type: Expr) -> Option:
        """Construct `Option.none` for `elem_type`."""
        return cls(EApp(EConst(cls.NONE_NAME, ()), elem_type))

    @classmethod
    def some(cls, elem_type: Expr, value: DeclaredType | Expr) -> Option:
        """Construct `Option.some value` for `elem_type`."""
        value_expr = cls.to_expr(value)
        return cls(EApp(EApp(EConst(cls.SOME_NAME, ()), elem_type), value_expr))

    @classmethod
    def eq(cls, *args: DeclaredType | Expr) -> Expr:
        """Construct `left = right` over `Option elem_type`."""
        if len(args) != cls.EQ_ARITY:
            raise TypeError(
                f"Option.eq expects {cls.EQ_ARITY} arguments, got {len(args)}"
            )
        elem_type, left, right = args
        left_expr = cls.to_expr(left)
        right_expr = cls.to_expr(right)
        return EApp(
            EApp(EApp(EConst(cls.EQ_NAME, ()), cls.type(elem_type)), left_expr),
            right_expr,
        )
