"""Tactics for introducing local variables into the current goal."""
from __future__ import annotations

from ..ast import EFVar, ELam, EMetaVar, EPi
from ..errors import TacticError
from ..framework.bound_var import instantiate_binder_body
from ..kernel import Goal, ProofManager, whnf
from .helpers import require_current_goal, requires_active_goal


@requires_active_goal
def intro(manager: ProofManager, name: str) -> None:
    """Introduce one variable from a dependent product goal."""
    state = manager.current_state
    current_goal = require_current_goal(manager)

    goal_expr = whnf(current_goal.statement, state.metavars, manager.env)
    if not isinstance(goal_expr, EPi):
        raise TacticError(
            f"Current goal is not a product type (EPi). Found: {goal_expr}"
        )

    if current_goal.has_local_hypothesis(name):
        raise TacticError(
            f"Identifier '{name}' already exists in the local context."
        )

    new_subgoal_statement = instantiate_binder_body(
        body=goal_expr.body,
        replacement=EFVar(name),
    )

    extended_local_context = current_goal.local_context | {name: goal_expr.domain}
    new_subgoal = Goal(
        statement=new_subgoal_statement,
        context=current_goal.global_context | extended_local_context,
        local_hypothesis_names=frozenset(extended_local_context.keys()),
    )

    assignment = ELam(
        var=name,
        domain=goal_expr.domain,
        body=EMetaVar(new_subgoal.id)
    )

    manager.refine_goal(assignment, [new_subgoal])


def intros(manager: ProofManager, names: list[str]) -> None:
    """Introduce multiple variables from a dependent product goal."""
    for name in names:
        intro(manager, name)
