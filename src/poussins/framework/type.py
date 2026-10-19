"""Type expression wrapper."""
from __future__ import annotations

from dataclasses import dataclass
from typing import override

from poussins.ast.universe import UnivLevelZero

from ..ast import ESort, EVar, Expr, Sort, UnivLevel, UnivLevelParam, UnivLevelSucc
from .bindable_mixin import BindableMixin


@dataclass(frozen=True, init=False)
class Type(BindableMixin):
    """Immutable wrapper for type expressions."""

    value: Expr
    level: UnivLevel

    def __init__(
        self,
        value: Expr | str,
        level: UnivLevel | int | str = Sort.TYPE.level
    ) -> None:
        """Initialize a type expression."""
        if isinstance(value, Expr):
            object.__setattr__(self, "value", value)
        else:
            object.__setattr__(self, "value", EVar(value))

        if isinstance(level, UnivLevel):
            object.__setattr__(self, "level", level)
        elif isinstance(level, int):
            if level < 0:
                raise ValueError("Level must be a non-negative integer.")
            else:
                lv = UnivLevelZero()
                for _ in range(level):
                    lv = UnivLevelSucc(lv)

                object.__setattr__(self, "level", lv)
        else:
            object.__setattr__(self, "level", UnivLevelParam(level))

    @property
    @override
    def bound_type(self) -> Expr:
        """Return the type of the bound variable."""
        return ESort(self.level)

    @property
    @override
    def bound_value(self) -> Expr:
        """Return the value of the bound variable."""
        return self.value
