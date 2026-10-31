"""Equality definition wrapper."""
from __future__ import annotations

from dataclasses import dataclass

from ...ast import Expr, Sort, app, lam, pi
from ...environment import const
from ...environment.library import EQ_IND_SPEC
from ..bound_var import BoundVarLike, normalize_bound_vars
from ..definition import Definition
from ..environment import STANDARD_ENV
from ..inductive import Inductive


@dataclass(frozen=True, init=False)
class Eq(Definition):
    """Immutable wrapper for equality definitions."""

    def __init__(
        self,
        name: str,
        bound_vars: BoundVarLike,
        type_a: Expr | type[Inductive],
        left: Inductive | Expr,
        right: Inductive | Expr,
    ) -> None:
        """Create an equality definition."""
        normalized = normalize_bound_vars(bound_vars)
        super().__init__(
            name=name,
            type_=pi(normalized, Sort.PROP.sort,),
            value=lam(
                normalized,
                app(
                    const(STANDARD_ENV, EQ_IND_SPEC.name),
                    (
                        type_a.type_ref()
                        if isinstance(type_a, type) and issubclass(type_a, Inductive)
                        else type_a
                    ),
                    Inductive.to_expr(left),
                    Inductive.to_expr(right),
                ),
            ),
        )
