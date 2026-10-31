"""Type expression wrapper."""
from __future__ import annotations

from dataclasses import dataclass
from typing import override

from ..ast import ESort, EVar, Expr, Sort, UnivLevel, univ_level
from .bound_var import BindableMixin


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
        object.__setattr__(
            self,
            "value",
            value if isinstance(value, Expr) else EVar(value)
        )
        object.__setattr__(self, "level", univ_level(level))

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
