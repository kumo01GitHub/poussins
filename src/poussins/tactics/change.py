"""Tactic for replacing the current goal or local hypothesis with a equal expression."""
from __future__ import annotations

from ..ast import Expr
from ..kernel import ProofManager
from .helpers import requires_active_goal


@requires_active_goal
def change(
    manager: ProofManager,
    expr: Expr,
    hypothesis_name: str | None = None
) -> None:
    """Replace the current goal with a definitionally equal expression."""
    if hypothesis_name is None:
        manager.change_goal(expr)
    else:
        manager.change_hypothesis(hypothesis_name, expr)
