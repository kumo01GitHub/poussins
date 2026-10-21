"""Vector: public-facing length-indexed vector DSL."""
from __future__ import annotations

from dataclasses import dataclass
from typing import ClassVar, override

from ...ast import EConst, Expr, build_app_chain
from ...environment.library import VectorDeclaration
from ..inductive import Inductive


@dataclass(frozen=True, init=False)
class Vector(Inductive):
    """Immutable wrapper for length-indexed vector expressions."""

    TYPE_NAME: ClassVar[str] = VectorDeclaration.VECTOR_DECLARATION.declaration.name
    LEVEL_PARAMS: ClassVar[tuple[str, ...]] = (
        VectorDeclaration.VECTOR_DECLARATION.declaration.level_params
    )

    def __class_getitem__(
        cls,
        item: tuple[type[Inductive] | Expr, Inductive | Expr],
    ) -> type[Vector]:
        """Return a new class representing a vector of given item type and length."""
        elem_item, length_item = item
        elem_expr = (
            elem_item.type_expr()
            if isinstance(elem_item, type) and issubclass(elem_item, Inductive)
            else elem_item
        )
        length_expr = cls.to_expr(length_item)

        @dataclass(frozen=True, init=False)
        class BoundVector(cls):
            @override
            @classmethod
            def type_expr(cls) -> Expr:
                return build_app_chain(Vector.type_expr(), elem_expr, length_expr)

            @classmethod
            def nil(cls) -> BoundVector:
                return cls(
                    build_app_chain(
                        EConst(
                            name=VectorDeclaration.VECTOR_NIL_DECLARATION.declaration.name,
                            levels=cls.levels(),
                        ),
                        elem_expr,
                    )
                )

            @classmethod
            def cons(
                cls,
                length: Inductive | Expr,
                head: Inductive | Expr,
                tail: BoundVector | Expr,
            ) -> BoundVector:
                return cls(
                    build_app_chain(
                        EConst(
                            name=VectorDeclaration.VECTOR_CONS_DECLARATION.declaration.name,
                            levels=cls.levels(),
                        ),
                        elem_expr,
                        cls.to_expr(length),
                        cls.to_expr(head),
                        cls.to_expr(tail),
                    )
                )

        return BoundVector
