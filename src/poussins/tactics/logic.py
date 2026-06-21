"""
Logic tactics: exfalso.
"""
from copy import deepcopy

from ..ast import FFalse, PMetaVar, PFalseE
from ..errors import TacticError
from ..kernel import ProofEngine, Goal


def exfalso(engine: ProofEngine):
    """Apply the exfalso tactic to derive a contradiction."""
    current_goal = engine.state.current_goal
    if current_goal is None:
        raise TacticError("No active goal to apply exfalso tactic.")

    subgoal = Goal(
        formula=FFalse(),
        context=current_goal.context
    )
    engine.refine_goal(
        [subgoal],
        assignment=PFalseE(
            inner=PMetaVar(goal_id=subgoal.id),
            conclusion=deepcopy(current_goal.formula)
        )
    )
