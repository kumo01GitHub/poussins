"""Spark worker node executor for ProofTaskNode."""
from __future__ import annotations

from typing import TypedDict

from ...environment import Environment, TheoremDeclaration
from .proof_script import SparkProofScript
from .proof_task import ProofTaskNode
from .serializer import (
    ProofTaskSerializer,
    SerializedNodeDict,
)


class TaskExecutionResult(TypedDict):
    """Execution result returned by a Spark worker after running a ProofTask."""

    task_name: str
    success: bool
    declaration: TheoremDeclaration | None
    error_message: str | None


class ProofTaskExecutor:
    """Executes proof tasks (ProofTaskNode) on Spark Worker nodes."""

    @classmethod
    def execute_task(
        cls,
        serialized_task: SerializedNodeDict,
        env: Environment,
    ) -> TaskExecutionResult:
        """Task execution entry point for PySpark worker nodes."""
        task_name = "<unknown>"
        try:
            node: ProofTaskNode = ProofTaskSerializer.deserialize_node(serialized_task)
            task_name = node.name

            script = SparkProofScript(node=node, env=env)
            script.execute_recipe()
            declaration = script.qed()

            return {
                "task_name": task_name,
                "success": True,
                "declaration": declaration,
                "error_message": None,
            }
        except Exception as e:
            return {
                "task_name": task_name,
                "success": False,
                "declaration": None,
                "error_message": str(e),
            }
