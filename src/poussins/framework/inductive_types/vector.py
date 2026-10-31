"""Vector: public-facing length-indexed vector DSL."""
from __future__ import annotations

from dataclasses import dataclass
from typing import ClassVar, override

from ...ast import Expr, app
from ...environment import const
from ...environment.library import VECTOR_IND_SPEC
from ..environment import STANDARD_ENV
from ..inductive import Inductive, inductive_type


@dataclass(frozen=True, init=False)
@inductive_type(spec=VECTOR_IND_SPEC)
class Vector(Inductive):
    """Immutable wrapper for length-indexed vector expressions."""

    NIL_IDX: ClassVar[int] = 0
    CONS_IDX: ClassVar[int] = 1

    def __class_getitem__(
        cls,
        item: tuple[type[Inductive] | Expr, Inductive | Expr],
    ) -> type[Vector]:
        """Return a new class representing a vector of given item type and length."""
        elem_item, length_item = item
        elem_expr = (
            elem_item.type_ref()
            if isinstance(elem_item, type) and issubclass(elem_item, Inductive)
            else elem_item
        )
        length_expr = cls.to_expr(length_item)

        @dataclass(frozen=True, init=False)
        class BoundVector(cls):
            @override
            @classmethod
            def type_ref(cls) -> Expr:
                return app(Vector.type_ref(), elem_expr, length_expr)

            @classmethod
            def nil(cls) -> BoundVector:
                env = cls.env()
                return cls(
                    app(
                        const(
                            env=env if env is not None else STANDARD_ENV,
                            name=VECTOR_IND_SPEC.constructors[cls.NIL_IDX][0],
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
                env = cls.env()
                return cls(
                    app(
                        const(
                            env=env if env is not None else STANDARD_ENV,
                            name=VECTOR_IND_SPEC.constructors[cls.CONS_IDX][0],
                        ),
                        elem_expr,
                        cls.to_expr(length),
                        cls.to_expr(head),
                        cls.to_expr(tail),
                    )
                )

        return BoundVector
