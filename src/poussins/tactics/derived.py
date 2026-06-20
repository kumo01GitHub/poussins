"""
Derived tactics.
"""
from typing import Optional

from .primitive import constructor, exact
from ..errors import TacticError
from ..framework import Environment
from ..kernel import ProofEngine
from ..tactics import intro


def intros(engine: ProofEngine, hyp_names: list[str]):
    for hyp_name in hyp_names:
        intro(engine, hyp_name)


def assumption(engine: ProofEngine, env: Optional[Environment]):
    current_goal = engine.state.current_goal
    if current_goal is None:
        raise TacticError("No active goal to apply assumption tactic.")

    for k, v in current_goal.context.hyps.items():
        if v == current_goal.formula:
            exact(engine, k, env)
            return
    if env is None:
        env = Environment()
    for k, v in env.declarations.items():
        if v.statement == current_goal.formula:
            exact(engine, k, env)
            return

    raise TacticError("No matching hypothesis found in the current context.")


def left(engine: ProofEngine):
    constructor(engine, idx=1)


def right(engine: ProofEngine):
    constructor(engine, idx=2)
