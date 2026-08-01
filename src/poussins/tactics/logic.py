from ..ast import EApp, EConst, EMetaVar
from ..errors import TacticError
from ..kernel import ProofManager, Goal


def exfalso(manager: ProofManager) -> None:
    """Exfalso tactic: Changes the target of the current goal from `P` to `False`."""
    if manager.is_closed:
        raise TacticError("exfalso failed: No active goals remain.")

    current_goal = manager.current_state.current_goal
    if current_goal is None:
        raise TacticError("exfalso failed: No active goals remain.")

    false_goal = Goal(
        statement=EConst("False", ()), context=current_goal.context
    )

    elim_expr = EApp(
        EApp(EConst("False.elim", ()), current_goal.statement),
        EMetaVar(false_goal.id),
    )

    manager.refine_goal(elim_expr, [false_goal])
