"""Equality definition wrapper."""
from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass

from ...ast import EConst, Expr, Sort, app, lam, pi, univ_levels
from ...environment import Environment
from ...environment.library import EqualityDeclaration
from ..binding import BindingLike, normalize_bindings
from ..definition import Definition
from ..inductive import Inductive


@dataclass(frozen=True, init=False)
class Eq(Definition):
    """Immutable wrapper for equality definitions."""

    def __init__(
        self,
        env: Environment,
        name: str,
        bindings: BindingLike,
        type_a: Expr,
        left: Inductive | Expr,
        right: Inductive | Expr,
        level_params: Sequence[str] = (),
    ) -> None:
        """Create an equality definition."""
        normalized = normalize_bindings(bindings)
        super().__init__(
            env=env,
            name=name,
            type_=pi(normalized, Sort.PROP.sort,),
            value=lam(
                normalized,
                app(
                    EConst(
                        name=EqualityDeclaration.EQ_DECLARATION.declaration.name,
                        levels=univ_levels(EqualityDeclaration.EQ_DECLARATION.declaration.level_params),
                    ),
                    type_a,
                    Inductive.to_expr(left),
                    Inductive.to_expr(right),
                ),
            ),
            level_params=level_params,
        )
