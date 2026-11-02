"""Spark worker node executor for ProofTaskNode."""
from __future__ import annotations

from copy import deepcopy
from typing import TypedDict

from ...environment import Environment, TheoremDeclaration, TheoremSpec
from ...errors import SparkIntegrationError
from ...framework import declare_theorem
from ...framework.tactic_mixin import TacticMixin
from ...kernel import ProofManager
from ...utils.logging import get_logger
from ..tactic import TacticPlan
from .task import ProofTaskNode


class TaskExecutionResult(TypedDict):
    """Execution result returned by a Spark worker after running a ProofTask."""

    task_name: str
    success: bool
    declaration: TheoremDeclaration | None
    error_message: str | None


class ProofTaskExecutor(TacticMixin):
    """Executes proof tasks (ProofTaskNode) on Spark Worker nodes."""

    def __init__(self, task: ProofTaskNode, env: Environment) -> None:
        """Initialize worker-local proof state for a single task execution."""
        worker_env = deepcopy(env)
        TacticMixin.__init__(
            self,
            manager=ProofManager(task.statement, worker_env),
            logger=get_logger(__name__),
        )
        self._task_name = task.name
        self._task: ProofTaskNode = task
        self._env: Environment = worker_env

    def execute_plan(self, plan: list[TacticPlan] | None = None) -> None:
        """Sequentially execute serialized tactics for the current task."""
        execution_plan = self._task.tactic_plan if plan is None else plan
        for tactic_name, kwargs in execution_plan:
            tactic_fn = getattr(self, tactic_name, None)
            if tactic_fn is None or not callable(tactic_fn):
                raise SparkIntegrationError(
                    f"Unknown tactic '{tactic_name}' requested"
                    f" in task '{self._task_name}'."
                )
            tactic_fn(**kwargs)

    def declare(self) -> TheoremDeclaration:
        """Validate closure and declare theorem in the worker-local environment."""
        if not self.is_closed:
            raise SparkIntegrationError(
                f"Theorem '{self._task_name}' cannot be closed:"
                + " The proof is not finished."
            )

        term = self.manager.current_term
        if term is None:
            raise SparkIntegrationError(
                f"Theorem '{self._task_name}' internal error:"
                + " Failed to extract a valid proof term."
            )

        return declare_theorem(
            self._env,
            TheoremSpec(
                name=self._task_name,
                statement=self._task.statement,
                term=term,
            ),
        )

    def execute(self) -> TaskExecutionResult:
        """Run the assigned task and return a structured worker result."""
        try:
            self.logger.info(
                f"Starting proof task execution on Worker: '{self._task_name}'"
            )
            self.execute_plan()
            declaration = self.declare()

            self.logger.info(
                f"Successfully completed proof task: '{self._task_name}'"
            )
            return {
                "task_name": self._task_name,
                "success": True,
                "declaration": declaration,
                "error_message": None,
            }
        except Exception as e:
            self.logger.error(
                f"Failed to execute proof task '{self._task_name}': {e}",
                exc_info=True,
            )
            return {
                "task_name": self._task_name,
                "success": False,
                "declaration": None,
                "error_message": str(e),
            }
