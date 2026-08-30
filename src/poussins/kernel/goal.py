"""Kernel-level goal representation for the proof system."""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import override
from uuid import uuid4

from ..ast.expr import Expr


@dataclass(frozen=True)
class Goal:
    """A single proof subgoal, consisting of a statement and a visible context.

    The stored ``context`` is the merged global+local view used by the kernel,
    while ``local_hypothesis_names`` tracks which entries are local binders or
    hypotheses and may shadow globals.
    """

    id: str = field(default_factory=lambda: str(uuid4()), init=False)
    statement: Expr
    context: dict[str, Expr]
    local_hypothesis_names: frozenset[str] | None = None

    def __post_init__(self) -> None:
        """Ensure that local_hypothesis_names is initialized."""
        if self.local_hypothesis_names is None:
            object.__setattr__(
                self,
                "local_hypothesis_names",
                frozenset(self.context.keys())
            )

    @property
    def local_context(self) -> dict[str, Expr]:
        """Return the local hypotheses and binders in scope for this goal."""
        return {
            name: self.context[name]
            for name in self.local_hypothesis_names if name in self.context
        }

    @property
    def global_context(self) -> dict[str, Expr]:
        """Return the visible global declarations for this goal."""
        return {
            name: typ for name, typ in self.context.items() if name not in self.local_hypothesis_names
        }

    def has_local_hypothesis(self, name: str) -> bool:
        """Return whether the given name belongs to the local context."""
        return name in self.local_hypothesis_names

    def with_statement(self, statement: Expr) -> Goal:
        """Return a goal with the same identifier and context but a new statement."""
        updated = Goal(
            statement=statement,
            context=dict(self.context),
            local_hypothesis_names=self.local_hypothesis_names,
        )
        object.__setattr__(updated, "id", self.id)
        return updated

    def with_context(
        self,
        context: dict[str, Expr],
        local_hypothesis_names: frozenset[str] | None = None,
    ) -> Goal:
        """Return a goal with the same identifier and statement but a new context."""
        updated = Goal(
            statement=self.statement,
            context=context,
            local_hypothesis_names=(
                self.local_hypothesis_names
                if local_hypothesis_names is None else local_hypothesis_names
            ),
        )
        object.__setattr__(updated, "id", self.id)
        return updated

    @override
    def __eq__(self, other: object) -> bool:
        """Compare goals by their stable identifier."""
        if not isinstance(other, Goal):
            return False
        return self.id == other.id

    @override
    def __hash__(self) -> int:
        """Compute the hash based on the stable identifier."""
        return hash(self.id)
