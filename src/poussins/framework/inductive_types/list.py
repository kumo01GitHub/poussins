"""List: public-facing list-value DSL."""
from __future__ import annotations

from dataclasses import dataclass
from typing import ClassVar, override

from ...ast import Expr, app
from ...environment import const
from ...environment.library import LIST_IND_SPEC
from ..environment import STANDARD_ENV
from ..inductive import Inductive, inductive_type


@dataclass(frozen=True, init=False)
@inductive_type(spec=LIST_IND_SPEC)
class List(Inductive):
    """Immutable wrapper for list expressions."""

    NIL_IDX: ClassVar[int] = 0
    CONS_IDX: ClassVar[int] = 1

    def __class_getitem__(cls, item: type[Inductive] | Expr) -> type[List]:
        """Return a new class representing a list of the given item type."""
        elem_expr = (
            item.type_ref()
            if isinstance(item, type) and issubclass(item, Inductive)
            else item
        )

        @dataclass(frozen=True, init=False)
        class BoundList(cls):
            @override
            @classmethod
            def type_ref(cls) -> Expr:
                return app(List.type_ref(), elem_expr)

            @classmethod
            def nil(cls) -> BoundList:
                env = cls.env()
                return cls(
                    app(
                        const(
                            env=env if env is not None else STANDARD_ENV,
                            name=LIST_IND_SPEC.constructors[cls.NIL_IDX][0],
                        ),
                        elem_expr,
                    )
                )

            @classmethod
            def cons(cls, head: Inductive | Expr, tail: BoundList | Expr) -> BoundList:
                env = cls.env()
                return cls(
                    app(
                        const(
                            env=env if env is not None else STANDARD_ENV,
                            name=LIST_IND_SPEC.constructors[cls.CONS_IDX][0],
                        ),
                        elem_expr,
                        cls.to_expr(head),
                        cls.to_expr(tail),
                    )
                )

        return BoundList
