"""Tactic for removing a local hypothesis from the current goal context."""
from __future__ import annotations

from ..ast import EMetaVar, collect_free_vars
from ..errors import TacticError
from ..kernel import Goal, ProofManager
from .helpers import require_current_goal, requires_active_goal


@requires_active_goal
def clear(manager: ProofManager, hyp_name: str) -> None:
    """Remove a local hypothesis from the current goal context."""
    current_goal = require_current_goal(manager)

    if hyp_name not in current_goal.local_context:
        raise TacticError(f"Hypothesis '{hyp_name}' not found in local context.")

    if hyp_name in collect_free_vars(current_goal.statement):
        raise TacticError(
            f"Cannot clear '{hyp_name}' because it is still used in the target."
        )

    for name, expr in current_goal.local_context.items():
        if name != hyp_name and hyp_name in collect_free_vars(expr):
            raise TacticError(
                f"Cannot clear '{hyp_name}' because '{name}' depends on it."
            )

    new_goal = Goal(
        statement=current_goal.statement,
        context={
            name: expr
            for name, expr in current_goal.context.items()
            if name != hyp_name
        },
        local_hypothesis_names=(
            current_goal.local_hypothesis_names - {hyp_name}
            if current_goal.local_hypothesis_names is not None
            else None
        ),
    )

    manager.refine_goal(EMetaVar(new_goal.id), [new_goal])
