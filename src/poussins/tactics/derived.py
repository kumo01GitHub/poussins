"""
Derived tactics.
"""
from .primitive import exact
from ..ast import Formula
from ..errors import TacticError
from ..kernel import ProofEngine
from ..tactics import intro


def intros(proof_engine: ProofEngine, hyp_names: list[str]):
    for hyp_name in hyp_names:
        intro(proof_engine, hyp_name)

def assumption(proof_engine: ProofEngine):
    current_goal = proof_engine.state.current_goal
    if current_goal is None:
        raise TacticError("No active goal to apply assumption tactic.")

    for k, v in current_goal.context.hyps.items():
        if v == current_goal.formula:
            exact(proof_engine, k)
            return

    raise TacticError("No matching hypothesis found in the current context.")
