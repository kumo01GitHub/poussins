"""Spark worker node executor for ProofTaskNode."""
from __future__ import annotations

from typing import TypedDict

from ...environment import Environment, TheoremDeclaration
from ...utils.logging import get_logger
from .proof_script import SparkProofScript
from .serializer import (
    ProofTaskSerializer,
    SerializedNodeDict,
)
from .task import ProofTaskNode


class TaskExecutionResult(TypedDict):
    """Execution result returned by a Spark worker after running a ProofTask."""

    task_name: str
    success: bool
    declaration: TheoremDeclaration | None
    error_message: str | None


class ProofTaskExecutor:
    """Executes proof tasks (ProofTaskNode) on Spark Worker nodes."""

    def __init__(self) -> None:
        """Initialize the ProofTaskExecutor."""
        self.logger = get_logger(__name__)

    def execute_task(
        self,
        serialized_task: SerializedNodeDict,
        env: Environment,
    ) -> TaskExecutionResult:
        """Task execution entry point for PySpark worker nodes."""
        task_name = "<unknown>"
        try:
            node: ProofTaskNode = ProofTaskSerializer.deserialize_node(serialized_task)
            task_name = node.name
            self.logger.info(f"Starting proof task execution on Worker: '{task_name}'")

            script = SparkProofScript(node=node, env=env)
            script.execute_recipe()
            declaration = script.qed()

            self.logger.info(f"Successfully completed proof task: '{task_name}'")
            return {
                "task_name": task_name,
                "success": True,
                "declaration": declaration,
                "error_message": None,
            }
        except Exception as e:
            self.logger.error(
                f"Failed to execute proof task '{task_name}': {e}",
                exc_info=True,
            )
            return {
                "task_name": task_name,
                "success": False,
                "declaration": None,
                "error_message": str(e),
            }
