"""
Intro tactic: introduces a new hypothesis for an implication goal, generating a subgoal for the consequent."""
from copy import deepcopy

from ..ast import FImpl, PLam, PMetaVar
from ..errors import TacticError
from ..kernel import Goal, ProofEngine


def intro(engine: ProofEngine, hyp_name: str):
    """Introduce a new hypothesis."""
    current_goal = engine.state.current_goal
    if current_goal is None:
        raise TacticError("No active goal to apply intro tactic.")
    elif not isinstance(current_goal.formula, FImpl):
        raise TacticError("Intro tactic can only be applied to implications.")

    subgoal = Goal(
        formula=deepcopy(current_goal.formula.consequent),
        context=current_goal.context.add(
            { hyp_name: deepcopy(current_goal.formula.antecedent) }
        )
    )
    engine.refine_goal(
        [subgoal],
        assignment=PLam(
            var=hyp_name,
            dom=deepcopy(current_goal.formula.antecedent),
            body=PMetaVar(goal_id=subgoal.id)
        )
    )


def intros(engine: ProofEngine, hyp_names: list[str]):
    for hyp_name in hyp_names:
        intro(engine, hyp_name)
