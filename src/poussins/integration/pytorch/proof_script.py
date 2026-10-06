"""PyTorch-integrated ProofScript for AI-assisted automated proofs."""
from __future__ import annotations

from typing import Final, override

from ...ast import Expr
from ...environment import Environment, TheoremDeclaration
from ...errors import PyTorchIntegrationError
from ...framework import ProofScript
from ...utils.logging import get_logger
from ..tactic import TacticPlan
from .planner import AITacticPlanner


class PyTorchProofScript(ProofScript):
    """A ProofScript variant integrated with PyTorch AI tactic execution."""

    def __init__(
        self,
        statement: Expr,
        env: Environment,
        name: str = "ai_theorem",
        level_params: tuple[str, ...] = (),
    ) -> None:
        """Initialize script with statement, environment, and declaration info."""
        super().__init__(statement, env)
        self.name: Final[str] = name
        self.level_params: Final[tuple[str, ...]] = level_params
        self.history_plan: list[TacticPlan] = []
        self.logger = get_logger(__name__)

    def execute_plan(self, plan: list[TacticPlan]) -> None:
        """Sequentially execute a list of tactic plans against this proof state."""
        for tactic_name, kwargs in plan:
            if not hasattr(self, tactic_name):
                msg = f"Unknown tactic '{tactic_name}' requested in '{self.name}'."
                raise PyTorchIntegrationError(msg)
            tactic_fn = getattr(self, tactic_name)
            tactic_fn(**kwargs)
            self.history_plan.append((tactic_name, kwargs))

    def auto_prove(self, planner: AITacticPlanner) -> list[TacticPlan]:
        """Automatically synthesize and execute a tactic plan using an AI planner.

        Returns:
            The synthesized and executed list of TacticPlans.

        """
        plan = planner.plan(self.statement, env=self.env)
        self.execute_plan(plan)
        return plan

    @override
    def qed(self) -> TheoremDeclaration:
        """Verify the proof status and construct a validated TheoremDeclaration."""
        if not self.is_closed:
            msg = f"Theorem '{self.name}' cannot be closed: Proof is not finished."
            raise PyTorchIntegrationError(msg)
        proof_term = self.manager.current_proof_term
        if proof_term is None:
            msg = (
                f"Theorem '{self.name}' internal error: "
                "Failed to extract proof term."
            )
            raise PyTorchIntegrationError(msg)

        return TheoremDeclaration(
            name=self.name,
            level_params=self.level_params,
            type=self.statement,
            value=proof_term,
        )
