"""Option: public-facing optional-value DSL."""
from __future__ import annotations

from dataclasses import dataclass
from typing import ClassVar, override

from ...ast import EConst, Expr, build_app_chain
from ...environment.library import OptionDeclaration
from ..inductive import Inductive


@dataclass(frozen=True, init=False)
class Option(Inductive):
    """Immutable wrapper for optional-value expressions."""

    TYPE_NAME: ClassVar[str] = OptionDeclaration.OPTION_DECLARATION.declaration.name
    LEVEL_PARAMS: ClassVar[tuple[str, ...]] = (
        OptionDeclaration.OPTION_DECLARATION.declaration.level_params
    )

    def __class_getitem__(cls, item: type[Inductive] | Expr) -> type[Option]:
        """Return a new class representing an option of the given item type."""
        elem_expr = (
            item.type_expr()
            if isinstance(item, type) and issubclass(item, Inductive)
            else item
        )

        class BoundOption(cls):
            @override
            @classmethod
            def type_expr(cls) -> Expr:
                return build_app_chain(Option.type_expr(), elem_expr)

            @classmethod
            def none(cls) -> BoundOption:
                return cls(
                    build_app_chain(
                        EConst(
                            name=OptionDeclaration.OPTION_NONE_DECLARATION.declaration.name,
                            levels=cls.levels(),
                        ),
                        elem_expr,
                    )
                )

            @classmethod
            def some(cls, value: Inductive | Expr) -> BoundOption:
                return cls(
                    build_app_chain(
                        EConst(
                            name=OptionDeclaration.OPTION_SOME_DECLARATION.declaration.name,
                            levels=cls.levels(),
                        ),
                        elem_expr,
                        cls.to_expr(value),
                    )
                )

        return BoundOption
