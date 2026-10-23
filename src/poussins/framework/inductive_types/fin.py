"""Fin: public-facing finite-index DSL."""
from __future__ import annotations

from dataclasses import dataclass
from typing import ClassVar, override

from ...ast import EConst, Expr, app
from ...environment.library import FinDeclaration
from ..inductive import Inductive


@dataclass(frozen=True, init=False)
class Fin(Inductive):
    """Immutable wrapper for finite-index expressions."""

    TYPE_NAME: ClassVar[str] = FinDeclaration.FIN_DECLARATION.declaration.name
    LEVEL_PARAMS: ClassVar[tuple[str, ...]] = (
        FinDeclaration.FIN_DECLARATION.declaration.level_params
    )

    def __class_getitem__(cls, item: Inductive | Expr) -> type[Fin]:
        """Return a new class representing Fin of given index."""
        index_expr = cls.to_expr(item)

        @dataclass(frozen=True, init=False)
        class BoundFin(cls):
            @override
            @classmethod
            def type_expr(cls) -> Expr:
                return app(Fin.type_expr(), index_expr)

            @classmethod
            def zero(cls) -> BoundFin:
                return cls(
                    app(
                        EConst(
                            name=FinDeclaration.FIN_ZERO_DECLARATION.declaration.name,
                            levels=cls.levels(),
                        ),
                        index_expr,
                    )
                )

            @classmethod
            def succ(cls, value: Inductive | Expr) -> BoundFin:
                return cls(
                    app(
                        EConst(
                            name=FinDeclaration.FIN_SUCC_DECLARATION.declaration.name,
                            levels=cls.levels(),
                        ),
                        index_expr,
                        cls.to_expr(value),
                    )
                )

        return BoundFin
