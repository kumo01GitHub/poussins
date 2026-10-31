"""Theorem, Lemma, Example: proof-carrying DSL objects."""
from __future__ import annotations

from copy import deepcopy
from typing import Final
from uuid import uuid4

from ..ast import Expr
from ..environment import Environment, TheoremDeclaration, TheoremSpec
from ..errors import FrameworkError
from ..kernel import ProofManager
from ..utils.logging import get_logger
from .declaration import declare_theorem
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
    ) -> None:
        """Create a theorem."""
        self.name: Final[str] = name
        self.statement: Final[Expr] = Prop.to_expr(statement)
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

        declaration = declare_theorem(
            self.env,
            TheoremSpec(
                name=self.name,
                statement=self.statement,
                term=proof_term,
            )
        )
        self.logger.info(
            f"Theorem '{self.name}' is successfully proved: {self.statement}"
        )
        self.logger.info(f"==> {proof_term}")

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
    ) -> None:
        """Create a anonymous theorem."""
        Theorem.__init__(
            self,
            name=f"__example:{uuid4()}__",
            env=deepcopy(env),
            statement=statement,
        )
