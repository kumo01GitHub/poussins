"""
Kernel-level definition of a single proof subgoal and local context.
"""
from __future__ import annotations
from dataclasses import dataclass, field
from uuid import uuid4

from ..ast.expr import Expr


@dataclass(frozen=True)
class Goal:
    """A single proof subgoal, consisting of a statement and a local context."""

    id: str = field(default_factory=lambda: str(uuid4()), init=False)
    statement: Expr
    context: dict[str, Expr]

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, Goal):
            return False
        return self.id == other.id
