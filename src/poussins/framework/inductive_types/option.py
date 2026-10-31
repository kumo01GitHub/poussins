"""Option: public-facing optional-value DSL."""
from __future__ import annotations

from dataclasses import dataclass
from typing import ClassVar, override

from ...ast import Expr, app
from ...environment import const
from ...environment.library import OPTION_IND_SPEC
from ..environment import STANDARD_ENV
from ..inductive import Inductive, inductive_type


@dataclass(frozen=True, init=False)
@inductive_type(spec=OPTION_IND_SPEC)
class Option(Inductive):
    """Immutable wrapper for optional-value expressions."""

    NONE_IDX: ClassVar[int] = 0
    SOME_IDX: ClassVar[int] = 1

    def __class_getitem__(cls, item: type[Inductive] | Expr) -> type[Option]:
        """Return a new class representing an option of the given item type."""
        elem_expr = (
            item.type_ref()
            if isinstance(item, type) and issubclass(item, Inductive)
            else item
        )
        @dataclass(frozen=True, init=False)
        class BoundOption(cls):
            @override
            @classmethod
            def type_ref(cls) -> Expr:
                return app(Option.type_ref(), elem_expr)

            @classmethod
            def none(cls) -> BoundOption:
                env = cls.env()
                return cls(
                    app(
                        const(
                            env=env if env is not None else STANDARD_ENV,
                            name=OPTION_IND_SPEC.constructors[cls.NONE_IDX][0],
                        ),
                        elem_expr,
                    )
                )

            @classmethod
            def some(cls, value: Inductive | Expr) -> BoundOption:
                env = cls.env()
                return cls(
                    app(
                        const(
                            env=env if env is not None else STANDARD_ENV,
                            name=OPTION_IND_SPEC.constructors[cls.SOME_IDX][0],
                        ),
                        elem_expr,
                        cls.to_expr(value),
                    )
                )

        return BoundOption
