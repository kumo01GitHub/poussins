"""Sum: public-facing sum-type DSL."""
from __future__ import annotations

from dataclasses import dataclass
from typing import ClassVar, override

from ...ast import EConst, Expr, build_app_chain
from ...environment.library import SumDeclaration
from ..inductive import Inductive


@dataclass(frozen=True, init=False)
class Sum(Inductive):
    """Immutable wrapper for sum-type expressions."""

    TYPE_NAME: ClassVar[str] = SumDeclaration.SUM_DECLARATION.declaration.name
    LEVEL_PARAMS: ClassVar[tuple[str, ...]] = (
        SumDeclaration.SUM_DECLARATION.declaration.level_params
    )

    def __class_getitem__(
        cls,
        item: tuple[type[Inductive] | Expr, type[Inductive] | Expr],
    ) -> type[Sum]:
        """Return a new class representing a sum of two types."""
        left_item, right_item = item
        left_expr = (
            left_item.type_expr()
            if isinstance(left_item, type) and issubclass(left_item, Inductive)
            else left_item
        )
        right_expr = (
            right_item.type_expr()
            if isinstance(right_item, type) and issubclass(right_item, Inductive)
            else right_item
        )

        @dataclass(frozen=True, init=False)
        class BoundSum(cls):
            @override
            @classmethod
            def type_expr(cls) -> Expr:
                return build_app_chain(Sum.type_expr(), left_expr, right_expr)

            @classmethod
            def inl(cls, value: Inductive | Expr) -> BoundSum:
                return cls(
                    build_app_chain(
                        EConst(
                            name=SumDeclaration.SUM_INL_DECLARATION.declaration.name,
                            levels=cls.levels(),
                        ),
                        left_expr,
                        right_expr,
                        cls.to_expr(value),
                    )
                )

            @classmethod
            def inr(cls, value: Inductive | Expr) -> BoundSum:
                return cls(
                    build_app_chain(
                        EConst(
                            name=SumDeclaration.SUM_INR_DECLARATION.declaration.name,
                            levels=cls.levels(),
                        ),
                        left_expr,
                        right_expr,
                        cls.to_expr(value),
                    )
                )

        return BoundSum
