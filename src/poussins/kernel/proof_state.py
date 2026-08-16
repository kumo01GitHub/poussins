"""
Kernel-level proof state management for tracking goals and metavariables.
"""
from __future__ import annotations
from dataclasses import dataclass, field
from typing import Optional

from ..ast.expr import Expr
from .goal import Goal


@dataclass(frozen=True)
class MetaVar:
    """
    Track a metavariable statement and its optional assignment.
    """

    statement: Expr
    assignment: Optional[Expr] = None

    @property
    def is_assigned(self) -> bool:
        """
        Return whether the metavariable has been assigned.
        """
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
        """
        Return the next active goal, if one exists.
        """
        return self.goals[0] if self.goals else None
