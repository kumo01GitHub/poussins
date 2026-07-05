"""
Axiom: a named proposition accepted without proof.
"""
from __future__ import annotations

from .environment import Declaration, Environment
from .prop import Prop
from ..ast import Expr
from ..kernel import ProofAssurance


class Axiom:
    def __init__(
            self, name: str, statement: Prop | Expr
    ) -> None:
        self.name = name
        self.statement = Prop.to_expr(statement)

    @property
    def assurance(self) -> ProofAssurance:
        return ProofAssurance.TRUSTED

    def declare(self, env: Environment):
        env.add_declaration(
            Declaration.axiom(
                name=self.name,
                statement=self.statement,
            )
        )
