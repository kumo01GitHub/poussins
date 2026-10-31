"""Sigma: public-facing dependent-pair DSL."""
from __future__ import annotations

from dataclasses import dataclass
from typing import ClassVar, override

from ...ast import Expr, app
from ...environment import const
from ...environment.library import SIGMA_IND_SPEC
from ..environment import STANDARD_ENV
from ..inductive import Inductive, inductive_type


@dataclass(frozen=True, init=False)
@inductive_type(spec=SIGMA_IND_SPEC)
class Sigma(Inductive):
    """Immutable wrapper for dependent-pair expressions."""

    MK_IDX: ClassVar[int] = 0

    def __class_getitem__(
        cls,
        item: tuple[type[Inductive] | Expr, type[Inductive] | Expr],
    ) -> type[Sigma]:
        """Return a new class representing a dependent pair type."""
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
        class BoundSigma(cls):
            @override
            @classmethod
            def type_ref(cls) -> Expr:
                return app(Sigma.type_ref(), left_expr, right_expr)

            @classmethod
            def mk(cls, left: Inductive | Expr, right: Inductive | Expr) -> BoundSigma:
                env = cls.env()
                return cls(
                    app(
                        const(
                            env=env if env is not None else STANDARD_ENV,
                            name=SIGMA_IND_SPEC.constructors[cls.MK_IDX][0],
                        ),
                        left_expr,
                        right_expr,
                        cls.to_expr(left),
                        cls.to_expr(right),
                    )
                )

        return BoundSigma
