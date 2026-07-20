from __future__ import annotations

from ..ast import ELam, EPi, EMetaVar, EVar, substitute_expr_var  
from ..errors import TacticError
from ..kernel import ProofManager, Goal, whnf


def intro(manager: ProofManager, var_name: str) -> None:
    """
    Intro tactic: Introduce a new variable for the current goal if it is a product type (EPi).
    """
    if manager.is_closed:
        raise TacticError("intro failed: No active goals remain.")

    state = manager.current_state
    current_goal = state.current_goal
    assert current_goal is not None

    goal_expr = whnf(current_goal.statement, state.metavars)
    if not isinstance(goal_expr, EPi):
        raise TacticError(f"intro failed: Current goal is not a product type (EPi). Found: {goal_expr}")

    if var_name in current_goal.context:
        raise TacticError(f"intro failed: Identifier '{var_name}' already exists in the local context.")

    new_subgoal_statement = substitute_expr_var(
        expr=goal_expr.body,
        var_name=goal_expr.var,
        replacement=EVar(var_name)
    )

    extended_context = current_goal.context | {var_name: goal_expr.domain}
    new_subgoal = Goal(statement=new_subgoal_statement, context=extended_context)

    assignment = ELam(
        var=var_name,
        domain=goal_expr.domain,
        body=EMetaVar(new_subgoal.id)
    )

    try:
        manager.refine_goal(assignment, [new_subgoal])
    except Exception as e:
        raise TacticError(f"intro failed during kernel verification: {e}") from e
