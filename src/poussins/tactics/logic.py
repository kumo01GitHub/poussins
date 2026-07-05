"""
Logic tactics: exfalso.
"""
from copy import deepcopy
from typing import Optional

from ..ast import ETop, EBot, PMetaVar, PTrueI, PFalseE, PVar
from ..errors import TacticError
from ..framework import Environment
from ..kernel import ProofEngine, Goal


def exfalso(engine: ProofEngine):
    """Apply the exfalso tactic to derive a contradiction."""
    current_goal = engine.state.current_goal
    if current_goal is None:
        raise TacticError("No active goal to apply exfalso tactic.")

    subgoal = Goal(
        formula=EBot(),
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

    if isinstance(current_goal.formula, ETop):
        engine.close_goal(PTrueI())
        return
    else:
        for k, v in current_goal.context.items():
            if v == current_goal.formula:
                engine.close_goal(PVar(name=k))
                return
        if env is None:
            env = Environment()
        for k, v in env.items():
            if v.has_statement and v.statement == current_goal.formula and v.assignment is not None:
                engine.close_goal(v.assignment)
                return

        raise TacticError("Current goal is not trivially true and cannot be closed with trivial tactic.")
