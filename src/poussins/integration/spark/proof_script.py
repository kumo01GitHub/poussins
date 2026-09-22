"""Spark ProofScript implementation for distributed proof execution."""
from __future__ import annotations

from typing import Final, override

from ...environment import Environment, TheoremDeclaration
from ...errors import SparkIntegrationError
from ...framework import ProofScript
from .proof_task import ProofTaskNode, TacticRecipeItem


class SparkProofScript(ProofScript):
    """A ProofScript variant optimized for Spark Worker-side execution.

    Directly executes tactic recipes and yields TheoremDeclaration without
    unnecessary Environment round-trips.
    """

    def __init__(
        self,
        node: ProofTaskNode,
        env: Environment,
        level_params: tuple[str, ...] = (),
    ) -> None:
        """Initialize the SparkProofScript with a ProofTaskNode and environment."""
        self.name: Final[str] = node.name
        self.level_params: Final[tuple[str, ...]] = level_params
        self.recipe: Final[list[TacticRecipeItem]] = node.tactic_recipe
        super().__init__(node.statement, env)

    def execute_recipe(self) -> None:
        """Sequentially executes tactic recipes sent from Master."""
        for tactic_name, kwargs in self.recipe:
            if not hasattr(self, tactic_name):
                raise SparkIntegrationError(
                    f"Unknown tactic '{tactic_name}' requested in task '{self.name}'."
                )
            tactic_fn = getattr(self, tactic_name)
            tactic_fn(**kwargs)

    @override
    def qed(self) -> TheoremDeclaration:
        """Verify the proof and directly returns TheoremDeclaration."""
        if not self.is_closed:
            raise SparkIntegrationError(
                f"Task '{self.name}' cannot be closed: Proof is not finished."
            )
        proof_term = self.manager.current_proof_term
        if proof_term is None:
            raise SparkIntegrationError(
                f"Task '{self.name}' internal error: Failed to extract proof term."
            )

        return TheoremDeclaration(
            name=self.name,
            level_params=self.level_params,
            type=self.statement,
            value=proof_term,
        )
