"""
Kernel-level proof state representing current substitutions and unsolved goals.
"""
from __future__ import annotations
from dataclasses import dataclass, field
from typing import Optional

from ..ast.expr import Expr
from .goal import Goal


@dataclass(frozen=True)
class MetaVar:
    statement: Expr
    assignment: Optional[Expr] = None

    @property
    def is_assigned(self) -> bool:
        return self.assignment is not None


@dataclass(frozen=True)
class ProofState:
    """
    Holds the active goals tuple and global meta-variable instantiations.
    This acts as a pure data repository managing the state of an interactive proof.
    """
    goals: tuple[Goal, ...] = field(default_factory=tuple)
    metavars: dict[str, MetaVar] = field(default_factory=dict)

    @property
    def current_goal(self) -> Optional[Goal]:
        return self.goals[0] if self.goals else None
