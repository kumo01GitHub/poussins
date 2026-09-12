"""Tactic for applying a theorem, hypothesis, or expression."""
from __future__ import annotations

from ..ast import EApp, EMetaVar, EPi, Expr, substitute_expr_var
from ..kernel import Goal, ProofManager, infer_type, whnf
from .helpers import require_current_goal, requires_active_goal


@requires_active_goal
def apply(manager: ProofManager, expr: Expr) -> None:
    """Apply an expression to the current goal."""
    state = manager.current_state
    current_goal = require_current_goal(manager)

    implicit_subgoals: list[Goal] = []
    assignment = expr
    current_type = whnf(
        infer_type(expr, current_goal.context, state.metavars, manager.env),
        state.metavars,
        manager.env,
    )

    while isinstance(current_type, EPi):
        new_goal = Goal(
            statement=current_type.domain,
            context=current_goal.context,
            local_hypothesis_names=current_goal.local_hypothesis_names,
        )
        implicit_subgoals.append(new_goal)

        assignment = EApp(assignment, EMetaVar(new_goal.id))

        current_type = whnf(
            substitute_expr_var(
                expr=current_type.body,
                var_name=current_type.var,
                replacement=EMetaVar(new_goal.id)
            ),
            state.metavars,
            manager.env,
        )

    if not implicit_subgoals:
        manager.close_goal(assignment)
    else:
        manager.refine_goal(assignment, implicit_subgoals)
