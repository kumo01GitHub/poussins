"""
Tactics for closing goals with exact terms or assumptions.
"""
from ..ast import Expr, EVar
from ..errors import TacticError
from ..kernel import ProofManager, is_def_eq


def exact(manager: ProofManager, expr: Expr) -> None:
    """
    Close the current goal with the given expression.
    """
    if manager.is_closed:
        raise TacticError("exact failed: No active goals remain.")

    manager.close_goal(expr)


def assumption(manager: ProofManager) -> None:
    """
    Close the current goal with a matching local hypothesis.
    """
    if manager.is_closed:
        raise TacticError("assumption failed: No active goals remain.")

    state = manager.current_state
    current_goal = state.current_goal
    if current_goal is None:
        raise TacticError("assumption failed: No active goals remain.")

    target = current_goal.statement
    context = current_goal.context
    metavars = state.metavars

    for hyp_name, hyp_type in context.items():
        if is_def_eq(hyp_type, target, context, metavars):
            manager.close_goal(EVar(hyp_name))
            return

    raise TacticError("assumption failed: No matching hypothesis found in context.")
