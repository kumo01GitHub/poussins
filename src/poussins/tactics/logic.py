"""
Logic tactics: exfalso.
"""
from copy import deepcopy
from typing import Optional

from ..ast import FTrue, FFalse, PMetaVar, PTrueI, PFalseE, PVar
from ..errors import TacticError
from ..framework import Environment
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


def trivial(engine: ProofEngine, env: Optional[Environment]):
    """Close the current goal if it is trivially true."""
    current_goal = engine.state.current_goal
    if current_goal is None:
        raise TacticError("No active goal to apply trivial tactic.")

    if isinstance(current_goal.formula, FTrue):
        engine.close_goal(PTrueI())
        return
    else:
        for k, v in current_goal.context.hyps.items():
            if v == current_goal.formula:
                engine.close_goal(PVar(name=k))
                return
        if env is None:
            env = Environment()
        for k, v in env.declarations.items():
            if v.statement == current_goal.formula:
                engine.close_goal(v.assignment)
                return

        raise TacticError("Current goal is not trivially true and cannot be closed with trivial tactic.")
