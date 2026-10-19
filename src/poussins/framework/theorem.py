"""Theorem, Lemma, Example: proof-carrying DSL objects."""
from __future__ import annotations

from typing import Final, override
from uuid import uuid4

from ..ast import Expr
from ..environment import Environment, TheoremDeclaration
from ..errors import FrameworkError
from ..kernel import ProofManager, register_theorem, validate_theorem
from ..utils.logging import get_logger
from .prop import Prop
from .tactic_mixin import TacticMixin


class Theorem(TacticMixin):
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
        self.statement: Final[Expr] = Prop.to_expr(statement)
        self.level_params: Final[tuple[str, ...]] = level_params
        self.env: Final[Environment] = env

        TacticMixin.__init__(
            self,
            manager=ProofManager(self.statement, self.env),
            logger=get_logger(__name__),
        )

        self.logger.info(f"Theorem '{self.name}': {self.statement}")

    def qed(self) -> TheoremDeclaration:
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
            register_theorem(self.env, declaration)
            self.logger.info(
                f"Theorem '{self.name}' is successfully proved: {self.statement}"
            )
            self.logger.info(f"==> {proof_term}")
        except Exception as e:
            raise FrameworkError("Failed to register theorem") from e

        return declaration


# Stylistic aliases for Theorem.
Lemma = Theorem
Proposition = Theorem
Corollary = Theorem
Fact = Theorem
Remark = Theorem
Property = Theorem


class Example(Theorem):
    """An anonymous proof for exploration or testing.

    Like Theorem but without a name and without registering to Environment.
    """

    def __init__(
        self,
        statement: Prop | Expr,
        env: Environment,
        level_params: tuple[str, ...] = (),
    ) -> None:
        """Create a anonymous theorem."""
        Theorem.__init__(
            self,
            name=f"__example:{uuid4()}__",
            env=env,
            statement=statement,
            level_params=level_params
        )

    @override
    def qed(self) -> TheoremDeclaration:
        """Verify the anonymity proof is complete."""
        if not self.is_closed:
            raise FrameworkError(
                "Example cannot be verified: The proof is not finished."
            )

        if self.manager.current_proof_term is None:
            raise FrameworkError(
                "Example internal error: Failed to extract a valid proof term."
            )

        declaration = TheoremDeclaration(
            name="__example__",
            level_params=(),
            type=self.statement,
            value=self.manager.current_proof_term,
        )

        try:
            validate_theorem(self.env, declaration)
            self.logger.info(f"Example is successfully proved: {self.statement}")
            self.logger.info(f"==> {self.manager.current_proof_term}")
        except Exception as e:
            raise FrameworkError("Failed to verify example") from e

        return declaration
