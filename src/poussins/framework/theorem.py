"""Theorem, Lemma, Example: proof-carrying DSL objects."""
from __future__ import annotations

from logging import Logger
from typing import Final, override

from ..ast import Expr
from ..environment import Environment, TheoremDeclaration
from ..errors import FrameworkError
from ..utils.logging import getLogger
from .proof_script import ProofScript
from .prop import Prop


class Theorem(ProofScript):
    """A named proposition together with an interactive proof session.

    Tactics can be applied as methods (via ProofScript) or as standalone functions
    — both styles are equivalent::

        th = Theorem("mp", (p >> q) >> p >> q, env)
        th.intro("hpq")          # method style
        intro(th.manager, "hpq")  # function style — also valid
        th.intro("hp")
        th.exact(EVar("hp"))
        th.qed(env)              # seals the proof and registers into env
    """

    def __init__(
        self,
        name: str,
        statement: Prop | Expr,
        env: Environment,
        level_params: tuple[str, ...] = (),
    ) -> None:
        """Create a theorem."""
        self.name: Final[str] = name
        self.level_params: Final[tuple[str, ...]] = level_params
        super().__init__(Prop.to_expr(statement), env)

        self.logger: Logger = getLogger(__name__)
        self.logger.info(f"Theorem '{self.name}': {self.statement}")

    @override
    def qed(self) -> None:
        """Qualify the theorem.

        Verify that the proof is closed, extract the final proof term,
        and register it into the given environment.
        """
        if not self.is_closed:
            raise FrameworkError(
                f"Theorem '{self.name}' cannot be closed: The proof is not finished."
            )

        proof_term = self.manager.current_proof_term
        if proof_term is None:
            raise FrameworkError(
                f"Theorem '{self.name}' internal error: "
                + "Failed to extract a valid proof term."
            )

        declaration = TheoremDeclaration(
            name=self.name,
            level_params=self.level_params,
            type=self.statement,
            value=proof_term,
        )

        try:
            self.env.add(declaration)
            self.logger.info(
                f"Theorem '{self.name}' is successfully proved: {self.statement}"
            )
            self.logger.info(f"==> {proof_term}")
        except ValueError as e:
            raise FrameworkError("Failed to register theorem") from e


# Stylistic aliases for Theorem.
Lemma = Theorem
Proposition = Theorem
Corollary = Theorem
Fact = Theorem
Remark = Theorem
Property = Theorem


class Example(ProofScript):
    """An anonymous proof for exploration or testing.

    Like Theorem but without a name and without registering to Environment.
    """

    def __init__(self, statement: Prop | Expr, env: Environment) -> None:
        """Create an anonymous proof script for the given statement."""
        pure_expr = Prop.to_expr(statement)
        super().__init__(pure_expr, env)

        self.logger: Logger = getLogger(__name__)
        self.logger.info(f"Example: {self.statement}")

    @override
    def qed(self) -> None:
        """Verify the anonymity proof is complete."""
        if not self.is_closed:
            raise FrameworkError(
                "Example cannot be verified: The proof is not finished."
            )

        if self.manager.current_proof_term is None:
            raise FrameworkError(
                "Example internal error: Failed to extract a valid proof term."
            )

        self.logger.info(f"Example is successfully proved: {self.statement}")
        self.logger.info(f"==> {self.manager.current_proof_term}")
