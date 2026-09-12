"""Tactic for refining the current goal."""
from __future__ import annotations

from ..ast import EMetaVar, Expr, collect_metavar_ids, substitute_metavar
from ..kernel import Goal, ProofManager, infer_metavar_types
from .helpers import require_current_goal, requires_active_goal


@requires_active_goal
def refine(manager: ProofManager, expr: Expr) -> None:
    """Refine current goal using an expression that may contain metavariables."""
    state = manager.current_state
    current_goal = require_current_goal(manager)

    meta_type_map = infer_metavar_types(
        expr=expr,
        expected_type=current_goal.statement,
        context=current_goal.context,
        metavars=state.metavars,
        env=manager.env,
    )

    user_meta_ids = collect_metavar_ids(expr)

    subgoals: list[Goal] = []
    assignment_expr = expr

    for user_id in user_meta_ids:
        target_statement = meta_type_map.get(user_id, current_goal.statement)

        new_goal = Goal(
            statement=target_statement,
            context=current_goal.context,
            local_hypothesis_names=current_goal.local_hypothesis_names,
        )
        subgoals.append(new_goal)

        assignment_expr = substitute_metavar(
            expr=assignment_expr,
            target_goal_id=user_id,
            replacement=EMetaVar(new_goal.id),
        )

    if not subgoals:
        manager.close_goal(assignment_expr)
    else:
        manager.refine_goal(assignment_expr, subgoals)
