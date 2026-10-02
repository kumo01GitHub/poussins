"""Vector: public-facing length-indexed vector DSL."""
from __future__ import annotations

from typing import ClassVar

from ..ast import EApp, EConst, Expr
from ..environment.library import VectorDeclaration
from .inductive_type import InductiveType


class Vector(InductiveType):
    """Immutable wrapper for vector expressions."""

    TYPE_NAME: ClassVar[str] = VectorDeclaration.VECTOR_DECLARATION.declaration.name
    NIL_NAME: ClassVar[str] = VectorDeclaration.VECTOR_NIL_DECLARATION.declaration.name
    CONS_NAME: ClassVar[str] = (
        VectorDeclaration.VECTOR_CONS_DECLARATION.declaration.name
    )

    @classmethod
    def type(cls, elem_type: Expr, length: InductiveType | Expr) -> Expr:
        """Return `Vector elem_type length`."""
        length_expr = cls.to_expr(length)
        return EApp(EApp(EConst(cls.TYPE_NAME, ()), elem_type), length_expr)

    @classmethod
    def nil(cls, elem_type: Expr) -> Vector:
        """Construct `Vector.nil` over `elem_type`."""
        return cls(EApp(EConst(cls.NIL_NAME, ()), elem_type))

    @classmethod
    def cons(
        cls,
        elem_type: Expr,
        length: InductiveType | Expr,
        head: InductiveType | Expr,
        tail: Vector | Expr,
    ) -> Vector:
        """Construct `Vector.cons head tail` over `elem_type` and `length`."""
        length_expr = cls.to_expr(length)
        head_expr = cls.to_expr(head)
        tail_expr = cls.to_expr(tail)
        return cls(
            EApp(
                EApp(
                    EApp(EApp(EConst(cls.CONS_NAME, ()), elem_type), length_expr),
                    head_expr,
                ),
                tail_expr,
            )
        )

    @classmethod
    def eq(
        cls,
        elem_type: Expr,
        length: InductiveType | Expr,
        left: InductiveType | Expr,
        right: InductiveType | Expr,
    ) -> Expr:
        """Construct `left = right` over `Vector elem_type length`."""
        left_expr = cls.to_expr(left)
        right_expr = cls.to_expr(right)
        return EApp(
            EApp(EApp(EConst(cls.EQ_NAME, ()), cls.type(elem_type, length)), left_expr),
            right_expr,
        )
