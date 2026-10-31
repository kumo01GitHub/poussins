"""Sum: public-facing sum-type DSL."""
from __future__ import annotations

from dataclasses import dataclass
from typing import ClassVar, override

from ...ast import Expr, app
from ...environment import const
from ...environment.library import SUM_IND_SPEC
from ..environment import STANDARD_ENV
from ..inductive import Inductive, inductive_type


@dataclass(frozen=True, init=False)
@inductive_type(spec=SUM_IND_SPEC)
class Sum(Inductive):
    """Immutable wrapper for sum-type expressions."""

    INL_IDX: ClassVar[int] = 0
    INR_IDX: ClassVar[int] = 1

    def __class_getitem__(
        cls,
        item: tuple[type[Inductive] | Expr, type[Inductive] | Expr],
    ) -> type[Sum]:
        """Return a new class representing a sum of two types."""
        left_item, right_item = item
        left_expr = (
            left_item.type_ref()
            if isinstance(left_item, type) and issubclass(left_item, Inductive)
            else left_item
        )
        right_expr = (
            right_item.type_ref()
            if isinstance(right_item, type) and issubclass(right_item, Inductive)
            else right_item
        )

        @dataclass(frozen=True, init=False)
        class BoundSum(cls):
            @override
            @classmethod
            def type_ref(cls) -> Expr:
                return app(Sum.type_ref(), left_expr, right_expr)

            @classmethod
            def inl(cls, value: Inductive | Expr) -> BoundSum:
                env = cls.env()
                return cls(
                    app(
                        const(
                            env=env if env is not None else STANDARD_ENV,
                            name=SUM_IND_SPEC.constructors[cls.INL_IDX][0],
                        ),
                        left_expr,
                        right_expr,
                        cls.to_expr(value),
                    )
                )

            @classmethod
            def inr(cls, value: Inductive | Expr) -> BoundSum:
                env = cls.env()
                return cls(
                    app(
                        const(
                            env=env if env is not None else STANDARD_ENV,
                            name=SUM_IND_SPEC.constructors[cls.INR_IDX][0],
                        ),
                        left_expr,
                        right_expr,
                        cls.to_expr(value),
                    )
                )

        return BoundSum
