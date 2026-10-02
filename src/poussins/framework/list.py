"""List: public-facing list-value DSL."""
from __future__ import annotations

from typing import ClassVar

from ..ast import EApp, EConst, Expr
from ..environment.library import ListDeclaration
from .inductive_type import InductiveType


class List(InductiveType):
    """Immutable wrapper for list expressions."""

    TYPE_NAME: ClassVar[str] = ListDeclaration.LIST_DECLARATION.declaration.name
    NIL_NAME: ClassVar[str] = ListDeclaration.LIST_NIL_DECLARATION.declaration.name
    CONS_NAME: ClassVar[str] = (
        ListDeclaration.LIST_CONS_DECLARATION.declaration.name
    )

    @classmethod
    def type(cls, elem_type: Expr) -> Expr:
        """Return `List elem_type`."""
        return EApp(EConst(cls.TYPE_NAME, ()), elem_type)

    @classmethod
    def nil(cls, elem_type: Expr) -> List:
        """Construct the empty list over `elem_type`."""
        return cls(EApp(EConst(cls.NIL_NAME, ()), elem_type))

    @classmethod
    def cons(
        cls,
        elem_type: Expr,
        head: InductiveType | Expr,
        tail: List | Expr,
    ) -> List:
        """Construct `head :: tail` over `elem_type`."""
        head_expr = cls.to_expr(head)
        tail_expr = cls.to_expr(tail)
        return cls(
            EApp(
                EApp(EApp(EConst(cls.CONS_NAME, ()), elem_type), head_expr),
                tail_expr,
            )
        )

    @classmethod
    def eq(
        cls, elem_type: Expr, left: InductiveType | Expr, right: InductiveType | Expr
    ) -> Expr:
        """Construct `left = right` over `List elem_type`."""
        left_expr = cls.to_expr(left)
        right_expr = cls.to_expr(right)
        return EApp(
            EApp(EApp(EConst(cls.EQ_NAME, ()), cls.type(elem_type)), left_expr),
            right_expr,
        )
