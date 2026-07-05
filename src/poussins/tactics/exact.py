"""
Exact tactic: closes the current goal with a matching hypothesis or declaration.
"""
from typing import Optional

from ..ast import  PVar
from ..errors import TacticError
from ..framework import Environment
from ..kernel import ProofEngine


def exact(engine: ProofEngine, hyp_name: str, env: Optional[Environment]):
    """Close the current goal with a hypothesis."""
    current_goal = engine.state.current_goal
    if current_goal is None:
        raise TacticError("No active goal to apply exact tactic.")

    hyp = current_goal.context.get(hyp_name)
    if hyp is not None:
        if hyp != current_goal.formula:
            raise TacticError(f"Hypothesis '{hyp_name}' does not match the current goal formula.")

        engine.close_goal(PVar(name=hyp_name))
        return
    else:
        if env is None:
            env = Environment()
        declaration = env.get(hyp_name)
        if declaration is not None and declaration.has_statement:
            if declaration.statement != current_goal.formula:
                raise TacticError(f"Declaration '{hyp_name}' does not match the current goal formula.")
            if declaration.assignment is None:
                raise TacticError(f"Declaration '{hyp_name}' has no proof assignment.")

            engine.close_goal(declaration.assignment)
            return

    raise TacticError(f"Hypothesis or declaration '{hyp_name}' not found in the current context.")


def assumption(engine: ProofEngine, env: Optional[Environment]):
    current_goal = engine.state.current_goal
    if current_goal is None:
        raise TacticError("No active goal to apply assumption tactic.")

    for k, v in current_goal.context.items():
        if v == current_goal.formula:
            exact(engine, k, env)
            return
    if env is None:
        env = Environment()
    for k, v in env.items():
        if v.has_statement and v.statement == current_goal.formula and v.assignment is not None:
            exact(engine, k, env)
            return

    raise TacticError("No matching hypothesis found in the current context.")
