"""Bound variable utilities."""
from __future__ import annotations

from abc import ABC, abstractmethod
from collections.abc import Sequence
from typing import cast

from ..ast import EVar, Expr

type BoundVar = tuple[str, Expr]
type BoundVarLike = Sequence[BoundVar | BindableMixin] | BoundVar | BindableMixin
BOUND_VAR_LEN = 2


def normalize_bound_vars(bound_vars: BoundVarLike) -> Sequence[BoundVar]:
    """Normalize bound variable　likes into a sequence of bound variables."""
    def is_bound_var(obj: object) -> bool:
        return (
            isinstance(obj, tuple)
            and len(obj) == BOUND_VAR_LEN
            and isinstance(obj[0], str)
            and isinstance(obj[1], Expr)
        )

    if not bound_vars:
        raise TypeError("bound_vars must be a non-empty sequence of bound variables or bindable objects")

    if is_bound_var(bound_vars):
        return (cast(BoundVar, bound_vars),)
    elif isinstance(bound_vars, BindableMixin):
        return (bound_vars.to_bound_var(),)
    else:
        normalized: Sequence[BoundVar] = []
        for var in bound_vars:
            if is_bound_var(var):
                normalized.append(cast(BoundVar, var))
            elif isinstance(var, BindableMixin):
                normalized.append(var.to_bound_var())
            else:
                raise TypeError(
                    f"Invalid bound variable: {var}. Must be a tuple of (name, type) or a BindableMixin instance."
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


    def to_bound_var(self) -> BoundVar:
        """Convert to a bound variable (name, type) tuple."""
        name = self.name
        if name is None:
            raise ValueError(
                "Cannot convert to bound variable: name is None"
            )

        return (name, self.bound_type)
