"""Module for defining axioms in the framework."""
from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass

from ..ast import Expr
from ..environment import AxiomDeclaration, Environment
from .declaration import declare_axiom
from .prop import Prop


@dataclass(frozen=True, init=False)
class Axiom:
    """Represent a proposition accepted without proof."""

    env: Environment
    name: str
    statement: Expr
    level_params: tuple[str, ...]

    def __init__(
        self,
        env: Environment,
        name: str,
        statement: Prop | Expr,
        level_params: Sequence[str] = (),
    ) -> None:
        """Create an axiom."""
        object.__setattr__(self, "env", env)
        object.__setattr__(self, "name", name)
        object.__setattr__(self, "statement", Prop.to_expr(statement))
        object.__setattr__(self, "level_params", tuple(level_params))

    def declare(self) -> AxiomDeclaration:
        """Declare the axiom in the environment."""
        return declare_axiom(
            env=self.env,
            name=self.name,
            statement=self.statement,
            level_params=self.level_params,
        )
