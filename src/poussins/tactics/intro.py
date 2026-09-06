"""Tactics for introducing local variables into the current goal."""
from __future__ import annotations

from ..ast import ELam, EMetaVar, EPi, EVar, substitute_expr_var
from ..errors import TacticError
from ..kernel import Goal, ProofManager, whnf
from .helpers import require_current_goal, requires_active_goal


@requires_active_goal
def intro(manager: ProofManager, var_name: str) -> None:
    """Introduce one variable from a dependent product goal."""
    state = manager.current_state
    current_goal = require_current_goal(manager)

    goal_expr = whnf(current_goal.statement, state.metavars, manager.env)
    if not isinstance(goal_expr, EPi):
        raise TacticError(
            f"Current goal is not a product type (EPi). Found: {goal_expr}"
        )

    if current_goal.has_local_hypothesis(var_name):
        raise TacticError(
            f"Identifier '{var_name}' already exists in the local context."
        )

    new_subgoal_statement = substitute_expr_var(
        expr=goal_expr.body,
        var_name=goal_expr.var,
        replacement=EVar(var_name)
    )

    extended_local_context = current_goal.local_context | {var_name: goal_expr.domain}
    new_subgoal = Goal(
        statement=new_subgoal_statement,
        context=current_goal.global_context | extended_local_context,
        local_hypothesis_names=frozenset(extended_local_context.keys()),
    )

    assignment = ELam(
        var=var_name,
        domain=goal_expr.domain,
        body=EMetaVar(new_subgoal.id)
    )

    manager.refine_goal(assignment, [new_subgoal])


def intros(manager: ProofManager, var_names: list[str]) -> None:
    """Introduce multiple variables from a dependent product goal."""
    for var_name in var_names:
        intro(manager, var_name)
