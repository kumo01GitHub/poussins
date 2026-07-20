from __future__ import annotations
from ..ast import EApp, EPi, EMetaVar, Expr
from ..ast.ops import substitute_expr_var  
from ..kernel import (
    ProofManager,
    Goal,
    infer_type, whnf
)
from ..errors import TacticError


def apply(manager: ProofManager, expr: Expr) -> None:
    """
    Apply tactic: Apply a theorem or a hypothesis expression (Expr) to the current goal.
    It matches the conclusion of the expression's type with the current goal,
    and generates new subgoals for each of the expression's premises.
    """
    if manager.is_closed:
        raise TacticError("apply failed: No active goals remain.")

    state = manager.current_state
    current_goal = state.current_goal
    assert current_goal is not None

    try:
        expr_type = infer_type(expr, current_goal.context, state.metavars)
    except Exception as e:
        raise TacticError(f"apply failed: Could not infer type of the given expression: {e}")

    premises: list[Expr] = []
    implicit_subgoals: list[Goal] = []
    
    current_type = whnf(expr_type, state.metavars)
    assignment = expr

    while isinstance(current_type, EPi):
        premises.append(current_type.domain)
        
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

    conclusion = current_type

    from ..kernel.typecheck import is_alpha_eq
    if not is_alpha_eq(whnf(conclusion, state.metavars), whnf(current_goal.statement, state.metavars)):
        raise TacticError(
            f"apply failed: Type mismatch.\n"
            f"The theorem concludes: {conclusion}\n"
            f"But current goal requires: {current_goal.statement}"
        )

    try:
        if not implicit_subgoals:
            manager.close_goal(expr)
        else:
            manager.refine_goal(assignment, implicit_subgoals)

    except Exception as e:
        raise TacticError(f"apply failed during kernel verification: {e}")
