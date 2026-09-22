"""Spark integration for proof task management and execution."""
from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass, field

from ...ast import Expr
from ...errors import SparkIntegrationError

# Type alias for allowable tactic argument values (excluding Any for type safety)
type TacticArgValue = str | int | float | bool | Expr | list[str] | None
type TacticRecipeItem = tuple[str, dict[str, TacticArgValue]]


@dataclass(frozen=True)
class ProofTaskNode:
    """Represents an atomic proof task to be dispatched to a Spark worker."""

    name: str
    statement: Expr
    tactic_recipe: list[TacticRecipeItem]
    depends_on: list[str] = field(default_factory=list)


class ProofTaskDAG:
    """Manages proof task dependencies (DAG) and resolves execution stages."""

    def __init__(self, tasks: Sequence[ProofTaskNode] | None = None) -> None:
        """Initialize the DAG with an optional list of proof tasks."""
        self._tasks: dict[str, ProofTaskNode] = {}
        if tasks:
            for task in tasks:
                self.add_task(task)

    def add_task(self, task: ProofTaskNode) -> None:
        """Register a proof task into the DAG."""
        if task.name in self._tasks:
            raise SparkIntegrationError(
                f"Task with name '{task.name}' is already registered."
            )
        self._tasks[task.name] = task

    def get_task(self, name: str) -> ProofTaskNode:
        """Retrieve a proof task by name."""
        if name not in self._tasks:
            raise SparkIntegrationError(f"Task '{name}' not found in DAG.")
        return self._tasks[name]

    def validate(self) -> None:
        """Validate that all dependencies exist and checks for circular references."""
        # 1. Check for unregistered dependencies
        for task in self._tasks.values():
            for dep in task.depends_on:
                if dep not in self._tasks:
                    raise SparkIntegrationError(
                        f"Task '{task.name}' depends on unregistered task '{dep}'."
                    )

        # 2. Check for circular dependencies using DFS
        visited: set[str] = set()
        in_stack: set[str] = set()

        def dfs(node_name: str) -> None:
            visited.add(node_name)
            in_stack.add(node_name)

            for dep in self._tasks[node_name].depends_on:
                if dep not in visited:
                    dfs(dep)
                elif dep in in_stack:
                    raise SparkIntegrationError(
                        "Circular dependency detected involving"
                       + f" '{node_name}' and '{dep}'."
                    )

            in_stack.remove(node_name)

        for name in self._tasks:
            if name not in visited:
                dfs(name)

    def compute_execution_stages(self) -> list[list[ProofTaskNode]]:
        """Perform topological sorting and returns parallelizable execution stages."""
        self.validate()

        # Calculate initial in-degrees (number of unresolved dependencies for each task)
        in_degree: dict[str, int] = {
            name: len(task.depends_on) for name, task in self._tasks.items()
        }

        # Build reverse lookup table: tasks that depend on a given task
        dependents: dict[str, list[str]] = {name: [] for name in self._tasks}
        for name, task in self._tasks.items():
            for dep in task.depends_on:
                dependents[dep].append(name)

        stages: list[list[ProofTaskNode]] = []
        resolved: set[str] = set()

        while len(resolved) < len(self._tasks):
            # Extract tasks with zero unresolved dependencies in the current iteration
            current_stage_names = [
                name
                for name, deg in in_degree.items()
                if deg == 0 and name not in resolved
            ]

            if not current_stage_names:
                raise SparkIntegrationError(
                    "Failed to resolve execution stages. Possible cycle."
                )

            current_stage_nodes = [self._tasks[name] for name in current_stage_names]
            stages.append(current_stage_nodes)

            # Mark tasks as resolved and decrement in-degrees for dependent tasks
            for name in current_stage_names:
                resolved.add(name)
                for dep_name in dependents[name]:
                    in_degree[dep_name] -= 1

        return stages
