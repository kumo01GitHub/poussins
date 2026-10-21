"""List: public-facing list-value DSL."""
from __future__ import annotations

from dataclasses import dataclass
from typing import ClassVar, override

from ...ast import EConst, Expr, build_app_chain
from ...environment.library import ListDeclaration
from ..inductive import Inductive


@dataclass(frozen=True, init=False)
class List(Inductive):
    """Immutable wrapper for list expressions."""

    TYPE_NAME: ClassVar[str] = ListDeclaration.LIST_DECLARATION.declaration.name
    LEVEL_PARAMS: ClassVar[tuple[str, ...]] = (
        ListDeclaration.LIST_DECLARATION.declaration.level_params
    )

    def __class_getitem__(cls, item: type[Inductive] | Expr) -> type[List]:
        """Return a new class representing a list of the given item type."""
        elem_expr = (
            item.type_expr()
            if isinstance(item, type) and issubclass(item, Inductive)
            else item
        )

        class BoundList(cls):
            @override
            @classmethod
            def type_expr(cls) -> Expr:
                return build_app_chain(List.type_expr(), elem_expr)

            @classmethod
            def nil(cls) -> BoundList:
                return cls(
                    build_app_chain(
                        EConst(
                            name=ListDeclaration.LIST_NIL_DECLARATION.declaration.name,
                            levels=cls.levels(),
                        ),
                        elem_expr,
                    )
                )

            @classmethod
            def cons(cls, head: Inductive | Expr, tail: BoundList | Expr) -> BoundList:
                return cls(
                    build_app_chain(
                        EConst(
                            name=ListDeclaration.LIST_CONS_DECLARATION.declaration.name,
                            levels=cls.levels(),
                        ),
                        elem_expr,
                        cls.to_expr(head),
                        cls.to_expr(tail),
                    )
                )

        return BoundList
