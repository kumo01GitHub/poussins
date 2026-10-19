"""Spark ProofScript implementation for distributed proof execution."""
from __future__ import annotations

from typing import Final, override

from ...environment import Environment, TheoremDeclaration
from ...errors import SparkIntegrationError
from ...framework import Theorem
from ...kernel import validate_theorem
from ..tactic import TacticPlan
from .task import ProofTaskNode


class SparkProofScript(Theorem):
    """A theorem variant optimized for Spark Worker-side execution.

    Directly executes tactic plans and yields TheoremDeclaration without
    unnecessary Environment round-trips.
    """

    def __init__(
        self,
        node: ProofTaskNode,
        env: Environment,
        level_params: tuple[str, ...] = (),
    ) -> None:
        """Initialize the SparkProofScript with a ProofTaskNode and environment."""
        self.plan: Final[list[TacticPlan]] = node.tactic_plan
        super().__init__(
            name=node.name,
            statement=node.statement,
            env=env,
            level_params=level_params,
        )

    def execute_plan(self) -> None:
        """Sequentially executes tactic plans sent from Master."""
        for tactic_name, kwargs in self.plan:
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

        if self.manager.current_proof_term is None:
            raise SparkIntegrationError(
                f"Task '{self.name}' internal error: Failed to extract proof term."
            )

        declaration = TheoremDeclaration(
            name=self.name,
            level_params=self.level_params,
            type=self.statement,
            value=self.manager.current_proof_term,
        )

        try:
            validate_theorem(self.env, declaration)
            self.logger.info(f"'{self.name}' is successfully proved: {self.statement}")
            self.logger.info(f"==> {self.manager.current_proof_term}")
        except Exception as e:
            raise SparkIntegrationError("Failed to validate theorem") from e

        return declaration
