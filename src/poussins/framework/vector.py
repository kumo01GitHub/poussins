"""Vector: public-facing length-indexed vector DSL."""
from __future__ import annotations

from typing import ClassVar

from ..ast import EApp, EConst, Expr
from ..environment.library import VectorDeclaration
from .declared_type import DeclaredType


class Vector(DeclaredType):
    """Immutable wrapper for vector expressions."""

    TYPE_NAME: ClassVar[str] = VectorDeclaration.VECTOR_DECLARATION.declaration.name
    NIL_NAME: ClassVar[str] = VectorDeclaration.VECTOR_NIL_DECLARATION.declaration.name
    CONS_NAME: ClassVar[str] = (
        VectorDeclaration.VECTOR_CONS_DECLARATION.declaration.name
    )
    TYPE_ARITY: ClassVar[int] = 2
    EQ_ARITY: ClassVar[int] = 4

    @classmethod
    def type(cls, *args: DeclaredType | Expr) -> Expr:
        """Return `Vector elem_type length`."""
        if len(args) != cls.TYPE_ARITY:
            raise TypeError(
                f"Vector.type expects {cls.TYPE_ARITY} arguments, got {len(args)}"
            )
        elem_type, length = args
        elem_type_expr = cls.to_expr(elem_type)
        length_expr = cls.to_expr(length)
        return EApp(EApp(EConst(cls.TYPE_NAME, ()), elem_type_expr), length_expr)

    @classmethod
    def nil(cls, elem_type: Expr) -> Vector:
        """Construct `Vector.nil` over `elem_type`."""
        return cls(EApp(EConst(cls.NIL_NAME, ()), elem_type))

    @classmethod
    def cons(
        cls,
        elem_type: Expr,
        length: DeclaredType | Expr,
        head: DeclaredType | Expr,
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
    def eq(cls, *args: DeclaredType | Expr) -> Expr:
        """Construct `left = right` over `Vector elem_type length`."""
        if len(args) != cls.EQ_ARITY:
            raise TypeError(
                f"Vector.eq expects {cls.EQ_ARITY} arguments, got {len(args)}"
            )
        elem_type, length, left, right = args
        left_expr = cls.to_expr(left)
        right_expr = cls.to_expr(right)
        return EApp(
            EApp(EApp(EConst(cls.EQ_NAME, ()), cls.type(elem_type, length)), left_expr),
            right_expr,
        )
