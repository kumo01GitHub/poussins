"""List: public-facing list-value DSL."""
from __future__ import annotations

from typing import ClassVar

from ..ast import EApp, EConst, Expr
from ..environment.library import ListDeclaration
from .declared_type import DeclaredType


class List(DeclaredType):
    """Immutable wrapper for list expressions."""

    TYPE_NAME: ClassVar[str] = ListDeclaration.LIST_DECLARATION.declaration.name
    NIL_NAME: ClassVar[str] = ListDeclaration.LIST_NIL_DECLARATION.declaration.name
    CONS_NAME: ClassVar[str] = (
        ListDeclaration.LIST_CONS_DECLARATION.declaration.name
    )
    TYPE_ARITY: ClassVar[int] = 1
    EQ_ARITY: ClassVar[int] = 3

    @classmethod
    def type(cls, *args: DeclaredType | Expr) -> Expr:
        """Return `List elem_type`."""
        if len(args) != cls.TYPE_ARITY:
            raise TypeError(
                f"List.type expects {cls.TYPE_ARITY} argument, got {len(args)}"
            )
        (elem_type,) = args
        return EApp(EConst(cls.TYPE_NAME, ()), cls.to_expr(elem_type))

    @classmethod
    def nil(cls, elem_type: Expr) -> List:
        """Construct the empty list over `elem_type`."""
        return cls(EApp(EConst(cls.NIL_NAME, ()), elem_type))

    @classmethod
    def cons(
        cls,
        elem_type: Expr,
        head: DeclaredType | Expr,
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
    def eq(cls, *args: DeclaredType | Expr) -> Expr:
        """Construct `left = right` over `List elem_type`."""
        if len(args) != cls.EQ_ARITY:
            raise TypeError(
                f"List.eq expects {cls.EQ_ARITY} arguments, got {len(args)}"
            )
        elem_type, left, right = args
        left_expr = cls.to_expr(left)
        right_expr = cls.to_expr(right)
        return EApp(
            EApp(EApp(EConst(cls.EQ_NAME, ()), cls.type(elem_type)), left_expr),
            right_expr,
        )
