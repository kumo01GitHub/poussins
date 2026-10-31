"""Module for defining axioms in the framework."""
from __future__ import annotations

from dataclasses import dataclass

from ..ast import Expr
from ..environment import AxiomDeclaration, AxiomSpec
from .declaration import declare_axiom
from .prop import Prop


@dataclass(frozen=True, init=False)
class Axiom:
    """Represent a proposition accepted without proof."""

    name: str
    statement: Expr

    def __init__(
        self,
        name: str,
        statement: Prop | Expr,
    ) -> None:
        """Create an axiom."""
        object.__setattr__(self, "name", name)
        object.__setattr__(self, "statement", Prop.to_expr(statement))

    def declare(self, env) -> AxiomDeclaration:
        """Declare the axiom in the environment."""
        return declare_axiom(
            env=env,
            spec=AxiomSpec(
                name=self.name,
                statement=self.statement,
            ),
        )
