"""Sigma: public-facing dependent-pair DSL."""
from __future__ import annotations

from dataclasses import dataclass
from typing import ClassVar, override

from ...ast import EConst, Expr, build_app_chain
from ...environment.library import SigmaDeclaration
from ..inductive import Inductive


@dataclass(frozen=True, init=False)
class Sigma[T1: Inductive | Expr, T2: Inductive | Expr](Inductive):
    """Immutable wrapper for dependent-pair expressions."""

    TYPE_NAME: ClassVar[str] = SigmaDeclaration.SIGMA_DECLARATION.declaration.name
    LEVEL_PARAMS: ClassVar[tuple[str, ...]] = (
        SigmaDeclaration.SIGMA_DECLARATION.declaration.level_params
    )

    def __class_getitem__(
        cls,
        item: tuple[type[Inductive] | Expr, type[Inductive] | Expr],
    ) -> type[Sigma]:
        """Return a new class representing a dependent pair type."""
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

        class BoundSigma(cls):
            @override
            @classmethod
            def type_expr(cls) -> Expr:
                return build_app_chain(Sigma.type_expr(), left_expr, right_expr)

            @classmethod
            def mk(cls, left: Inductive | Expr, right: Inductive | Expr) -> BoundSigma:
                return cls(
                    build_app_chain(
                        EConst(
                            name=SigmaDeclaration.SIGMA_MK_DECLARATION.declaration.name,
                            levels=cls.levels(),
                        ),
                        left_expr,
                        right_expr,
                        cls.to_expr(left),
                        cls.to_expr(right),
                    )
                )

        return BoundSigma
