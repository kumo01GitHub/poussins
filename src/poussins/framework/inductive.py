"""Inductive type expressions."""
from __future__ import annotations

from abc import ABC
from dataclasses import dataclass
from typing import ClassVar, override

from ..ast import (
    EApp,
    EConst,
    ESort,
    EVar,
    Expr,
    Sort,
    UnivLevel,
    UnivLevelMax,
    UnivLevelParam,
)
from ..environment.library import EqualityDeclaration
from .bindable_mixin import BindableMixin
from .prop import Prop


@dataclass(frozen=True)
class Inductive(BindableMixin, ABC):
    """Immutable wrapper for inductive type expressions."""

    TYPE_NAME: ClassVar[str] = "__undefined__"
    LEVEL_PARAMS: ClassVar[tuple[str, ...]] = ()

    value: Expr

    def __init__(self, value: Expr | str) -> None:
        """Initialize an inductive type."""
        if isinstance(value, Expr):
            object.__setattr__(self, "value", value)
        else:
            object.__setattr__(self, "value", EVar(value))

    @staticmethod
    def to_expr(value: Inductive | Expr) -> Expr:
        """Return the underlying expression."""
        return value.value if isinstance(value, Inductive) else value

    @classmethod
    def levels(cls) -> tuple[UnivLevel, ...]:
        """Return the universe levels of this inductive type."""
        return tuple(UnivLevelParam(param) for param in cls.LEVEL_PARAMS)

    @classmethod
    def sort(cls) -> ESort:
        """Return the sort of this inductive type."""
        if not cls.LEVEL_PARAMS:
            return Sort.TYPE.sort

        level: UnivLevel = UnivLevelParam(cls.LEVEL_PARAMS[0])
        for param in cls.LEVEL_PARAMS[1:]:
            level = UnivLevelMax(level, UnivLevelParam(param))

        return ESort(level)

    @classmethod
    def type_expr(cls) -> Expr:
        """Return the type expression of this inductive type."""
        return EConst(name=cls.TYPE_NAME, levels=cls.levels())

    @property
    def type(self) -> Expr:
        """Return the type expression of this inductive type instance."""
        return self.type_expr()

    @classmethod
    def eq(
        cls,
        left: Inductive | Expr,
        right: Inductive | Expr,
    ) -> Prop:
        """Construct an equality proposition over this inductive type."""
        return Prop(
            EApp(
                EApp(
                    EApp(
                        EConst(
                            EqualityDeclaration.EQ_DECLARATION.declaration.name,
                            (cls.sort().level,),
                        ),
                        cls.type_expr()
                    ),
                    cls.to_expr(left)
                ),
                cls.to_expr(right),
            )
        )

    @property
    @override
    def bound_type(self) -> Expr:
        """Return the type of the bound variable."""
        return self.type

    @property
    @override
    def bound_value(self) -> Expr:
        """Return the value of the bound variable."""
        return self.value
