"""Tactics for closing goals with exact terms or assumptions."""
from ..ast import EVar, Expr
from ..errors import TacticError
from ..kernel import ProofManager, is_def_eq
from .helpers import require_current_goal, requires_active_goal


@requires_active_goal
def exact(manager: ProofManager, expr: Expr) -> None:
    """Close the current goal with the given expression."""
    manager.close_goal(expr)


@requires_active_goal
def assumption(manager: ProofManager) -> None:
    """Close the current goal with a matching local hypothesis."""
    state = manager.current_state
    current_goal = require_current_goal(manager)

    target = current_goal.statement
    context = current_goal.context
    metavars = state.metavars

    for hyp_name, hyp_type in current_goal.local_context.items():
        if is_def_eq(hyp_type, target, context, metavars, manager.env):
            manager.close_goal(EVar(hyp_name))
            return

    raise TacticError("No matching hypothesis found in context.")
