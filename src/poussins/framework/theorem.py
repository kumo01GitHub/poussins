"""
Theorem, Lemma, Example: proof-carrying DSL objects.
"""
from __future__ import annotations

from .prop import Prop
from .proof_script import ProofScript
from ..ast import Expr
from ..environment import Environment, ConstantDeclaration
from ..errors import FrameworkError


class Theorem(ProofScript):
    """A named proposition together with an interactive proof session.

    Tactics can be applied as methods (via ProofScript) or as standalone
    functions — both styles are equivalent::

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
        level_params: tuple[str, ...] = ()
    ) -> None:
        self.name = name
        self.level_params = level_params
        super().__init__(Prop.to_expr(statement), env)

    def qed(self) -> None:
        """
        Verify that the proof is closed, extract the final proof term,
        and register it into the given environment.
        """
        if not self.is_closed:
            raise FrameworkError(f"Theorem '{self.name}' cannot be closed: The proof is not finished.")

        proof_term = self.manager.current_proof_term
        if proof_term is None:
            raise FrameworkError(f"Theorem '{self.name}' internal error: Failed to extract a valid proof term.")

        declaration = ConstantDeclaration(
            name=self.name,
            level_params=self.level_params,
            type=self.statement,
            value=proof_term
        )

        try:
            self.env.add(declaration)
        except ValueError as e:
            raise FrameworkError(f"Failed to register theorem: {e}")

        print(f"Theorem '{self.name}' successfully proved and registered as {proof_term}. ✨")


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

    def __init__(
        self,
        statement: Prop | Expr,
        env: Environment
    ) -> None:
        pure_expr = Prop.to_expr(statement)
        super().__init__(pure_expr, env)

    def qed(self) -> None:
        """Verify the anonymity proof is complete."""
        if not self.is_closed:
            raise FrameworkError("Example cannot be verified: The proof is not finished.")

        if self.manager.current_proof_term is None:
            raise FrameworkError("Example internal error: Failed to extract a valid proof term.")

        print(f"Example successfully verified as {self.manager.current_proof_term}! Q.E.D. 🎉")
