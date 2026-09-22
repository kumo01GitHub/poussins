"""Registry for managing proof tasks and constructing execution DAGs."""
from __future__ import annotations

from ...ast import Expr
from ...errors import SparkIntegrationError
from .proof_task import (
    ProofTaskDAG,
    ProofTaskNode,
    TacticRecipeItem,
)


class ProofTaskRegistry:
    """Registry for managing proof tasks and constructing execution DAGs."""

    def __init__(self) -> None:
        """Initialize an empty task registry."""
        self._tasks: dict[str, ProofTaskNode] = {}

    def register_task(
        self,
        name: str,
        statement: Expr,
        tactic_recipe: list[TacticRecipeItem],
        depends_on: list[str] | None = None,
    ) -> ProofTaskNode:
        """Register a proof task (lemma/theorem) into the registry."""
        if name in self._tasks:
            raise SparkIntegrationError(
                f"Proof task with name '{name}' is already registered."
            )

        deps = depends_on or []
        for dep in deps:
            if dep not in self._tasks:
                raise SparkIntegrationError(
                    f"Dependency '{dep}' for task '{name}' is not registered"
                    + " in the registry."
                )

        node = ProofTaskNode(
            name=name,
            statement=statement,
            tactic_recipe=tactic_recipe,
            depends_on=deps,
        )
        self._tasks[name] = node
        return node

    def build_dag(self) -> ProofTaskDAG:
        """Construct a ProofTaskDAG containing all registered tasks."""
        dag = ProofTaskDAG()
        for node in self._tasks.values():
            dag.add_task(node)
        return dag

    def get_task(self, name: str) -> ProofTaskNode | None:
        """Retrieve a registered proof task by name."""
        return self._tasks.get(name)

    def clear(self) -> None:
        """Clear all registered proof tasks."""
        self._tasks.clear()

    def __len__(self) -> int:
        """Return the number of registered proof tasks."""
        return len(self._tasks)
