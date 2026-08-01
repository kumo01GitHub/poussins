"""
Tactic for applying a theorem, hypothesis, or expression.
"""
from __future__ import annotations

from ..ast import (
    EApp, EPi, EMetaVar, Expr,
    substitute_expr_var
)
from ..kernel import ProofManager, Goal, infer_type, whnf
from ..errors import TacticError


def apply(manager: ProofManager, expr: Expr) -> None:
    """
    Apply an expression to the current goal.
    """
    if manager.is_closed:
        raise TacticError("apply failed: No active goals remain.")

    state = manager.current_state
    current_goal = state.current_goal
    if current_goal is None:
        raise TacticError("apply failed: No active goals remain.")

    implicit_subgoals: list[Goal] = []
    current_type = whnf(infer_type(expr, current_goal.context, state.metavars), state.metavars)
    assignment = expr

    while isinstance(current_type, EPi):
        new_goal = Goal(statement=current_type.domain, context=current_goal.context)
        implicit_subgoals.append(new_goal)

        assignment = EApp(assignment, EMetaVar(new_goal.id))
        
        current_type = whnf(
            substitute_expr_var(
                expr=current_type.body,
                var_name=current_type.var,
                replacement=EMetaVar(new_goal.id)
            ),
            state.metavars
        )

    try:
        if not implicit_subgoals:
            manager.close_goal(assignment)
        else:
            manager.refine_goal(assignment, implicit_subgoals)
    except Exception as e:
        raise TacticError(f"apply failed during kernel verification: {e}")
