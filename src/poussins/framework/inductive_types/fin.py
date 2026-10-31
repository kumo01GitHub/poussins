"""Fin: public-facing finite-index DSL."""
from __future__ import annotations

from dataclasses import dataclass
from typing import ClassVar, override

from ...ast import Expr, app
from ...environment import const
from ...environment.library import FIN_IND_SPEC
from ..environment import STANDARD_ENV
from ..inductive import Inductive, inductive_type


@dataclass(frozen=True, init=False)
@inductive_type(spec=FIN_IND_SPEC)
class Fin(Inductive):
    """Immutable wrapper for finite-index expressions."""

    ZERO_IDX: ClassVar[int] = 0
    SUCC_IDX: ClassVar[int] = 1

    def __class_getitem__(cls, item: Inductive | Expr) -> type[Fin]:
        """Return a new class representing Fin of given index."""
        index_expr = cls.to_expr(item)

        @dataclass(frozen=True, init=False)
        class BoundFin(cls):
            @override
            @classmethod
            def type_ref(cls) -> Expr:
                return app(Fin.type_ref(), index_expr)

            @classmethod
            def zero(cls) -> BoundFin:
                env = cls.env()
                return cls(
                    app(
                        const(
                            env=env if env is not None else STANDARD_ENV,
                            name=FIN_IND_SPEC.constructors[cls.ZERO_IDX][0],
                        ),
                        index_expr,
                    )
                )

            @classmethod
            def succ(cls, value: Inductive | Expr) -> BoundFin:
                env = cls.env()
                return cls(
                    app(
                        const(
                            env=env if env is not None else STANDARD_ENV,
                            name=FIN_IND_SPEC.constructors[cls.SUCC_IDX][0],
                        ),
                        index_expr,
                        cls.to_expr(value),
                    )
                )

        return BoundFin
