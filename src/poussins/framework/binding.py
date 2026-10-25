"""Bindable mixin for bindable objects."""
from __future__ import annotations

from abc import ABC, abstractmethod
from collections.abc import Sequence
from typing import cast

from ..ast import EVar, Expr

type Binding = tuple[str, Expr]
type BindingLike = Sequence[Binding | BindableMixin] | Binding | BindableMixin
BINDING_LEN = 2


def normalize_bindings(bindings: BindingLike) -> Sequence[Binding]:
    """Normalize bindings to a sequence of Binding tuples."""
    def is_binding(obj: object) -> bool:
        return (
            isinstance(obj, tuple)
            and len(obj) == BINDING_LEN
            and isinstance(obj[0], str)
            and isinstance(obj[1], Expr)
        )

    if not bindings:
        raise TypeError("bindings requires at least one binding")

    if is_binding(bindings):
        return (cast(Binding, bindings),)
    elif isinstance(bindings, BindableMixin):
        return (bindings.to_binding(),)
    else:
        normalized: Sequence[Binding] = []
        for binding in bindings:
            if is_binding(binding):
                normalized.append(cast(Binding, binding))
            elif isinstance(binding, BindableMixin):
                normalized.append(binding.to_binding())
            else:
                raise TypeError(
                    "bindings must be a Binding or BindableMixin instance"
                )

        return normalized


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
