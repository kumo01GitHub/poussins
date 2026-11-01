"""Bound variable utilities."""
from __future__ import annotations

from abc import ABC, abstractmethod
from collections.abc import Sequence
from typing import cast

from ..ast import EApp, EBVar, EConst, EFVar, ELam, EMetaVar, EPi, ESort, Expr
from ..ast.ops import instantiate_binder

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
        raise TypeError(
            "bound_vars must be a non-empty sequence of bound variables"
            + " or bindable objects"
        )

    if is_bound_var(bound_vars):
        return (cast(BoundVar, bound_vars),)
    elif isinstance(bound_vars, BindableMixin):
        return (bound_vars.to_bound_var(),)
    else:
        normalized: list[BoundVar] = []
        for var in bound_vars:
            if is_bound_var(var):
                normalized.append(cast(BoundVar, var))
            elif isinstance(var, BindableMixin):
                normalized.append(var.to_bound_var())
            else:
                raise TypeError(
                    f"Invalid bound variable: {var}."
                    + " Must be a tuple of (name, type) or a BindableMixin instance."
                )

        return normalized


def abstract_over_bound_vars(expr: Expr, bound_var_names: Sequence[str]) -> Expr:
    """Abstract free variables into de Bruijn bound variables."""
    if not bound_var_names:
        return expr

    name_to_index = {name: i for i, name in enumerate(reversed(bound_var_names))}

    def _abstract(e: Expr, depth: int) -> Expr:
        match e:
            case EFVar(name):
                idx = name_to_index.get(name)
                if idx is None:
                    return e
                return EBVar(depth + idx)
            case EApp(fn, arg):
                return EApp(_abstract(fn, depth), _abstract(arg, depth))
            case ELam(var, domain, body):
                return ELam(var, _abstract(domain, depth), _abstract(body, depth + 1))
            case EPi(var, domain, body):
                return EPi(var, _abstract(domain, depth), _abstract(body, depth + 1))
            case ESort() | EConst() | EBVar() | EMetaVar():
                return e

    return _abstract(expr, 0)


def instantiate_binder_body(body: Expr, replacement: Expr) -> Expr:
    """Instantiate one binder body represented with de Bruijn indices."""
    return instantiate_binder(body, replacement)


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
        if isinstance(value, EFVar):
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
