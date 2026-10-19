"""Bindable mixin for bindable objects."""
from __future__ import annotations

from abc import ABC, abstractmethod

from ..ast import EVar, Expr

type Binding = tuple[str, Expr]


class BindableMixin(ABC):
    """Mixin for bindable objects."""

    @property
    @abstractmethod
    def bound_type(self) -> Expr:
        """Return the type of the bound variable."""
        pass

    @property
    @abstractmethod
    def bound_value(self) -> Expr:
        """Return the value of the bound variable."""
        pass

    @property
    def name(self) -> str | None:
        """Return the name."""
        value = self.bound_value
        if isinstance(value, EVar):
            return value.name

        return None


    def to_binding(self) -> Binding:
        """Return the binding as a tuple of name and type."""
        name = self.name
        if name is None:
            raise ValueError(
                "Cannot convert to binding: bound value is not a variable."
            )

        return (name, self.bound_type)
