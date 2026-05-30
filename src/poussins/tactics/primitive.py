"""
"""

from copy import deepcopy

from poussins.ast.proof_terms import PLam, ProofTerm

from ..kernel.proof_engine import ProofEngine
from ..kernel.goal import Goal
from ..ast import Formula, FImpl, PMetaVar, PVar, PApp


def intro(proof_engine: ProofEngine, hyp_name: str):
    """Introduce a new hypothesis."""
    current_goal = proof_engine.state.current_goal
    if current_goal is None:
        raise ValueError("No active goal to apply intro tactic.")
    elif not isinstance(current_goal.formula, FImpl):
        raise ValueError("Intro tactic can only be applied to implications.")

    subgoal = Goal(
        formula=deepcopy(current_goal.formula.consequent),
        context=current_goal.context.add(
            { hyp_name: deepcopy(current_goal.formula.antecedent) }
        )
    )
    proof_engine.refine_goal(
        [subgoal],
        assignment=PLam(
            var=hyp_name,
            dom=deepcopy(current_goal.formula.antecedent),
            body=PMetaVar(goal_id=subgoal.id)
        )
    )


def exact(proof_engine: ProofEngine, hyp_name: str):
    """Close the current goal with a hypothesis."""
    current_goal = proof_engine.state.current_goal
    if current_goal is None:
        raise ValueError("No active goal to apply exact tactic.")

    hyp = current_goal.context.get(hyp_name)
    if hyp is None:
        raise ValueError(f"Hypothesis '{hyp_name}' not found in the current context.")
    elif hyp != current_goal.formula:
        raise ValueError(f"Hypothesis '{hyp_name}' does not match the current goal formula.")

    proof_engine.close_goal(PVar(name=hyp_name))


def apply(proof_engine: ProofEngine, hyp_name: str):
    current_goal = proof_engine.state.current_goal
    if current_goal is None:
        raise ValueError("No active goal to apply apply tactic.")

    hyp = current_goal.context.get(hyp_name)
    if hyp is None:
        raise ValueError(f"Hypothesis '{hyp_name}' not found in the current context.")
    elif hyp == current_goal.formula:
        exact(proof_engine, hyp_name)
    elif not isinstance(hyp, FImpl):
        raise ValueError(f"Hypothesis '{hyp_name}' is not an implication and cannot be applied.")

    subgoals, assignment = _apply(current_goal, hyp_name, hyp)
    proof_engine.refine_goal(subgoals=subgoals, assignment=assignment)


def _apply(
        current_goal: Goal,
        hyp_name: str,
        hyp: Formula,
        goals: list[Goal] = None,
        idx: int = 0
    ) -> tuple[list[Goal], ProofTerm]:
    if goals is None:
        goals = []

    if current_goal.formula == hyp:
        return goals, PVar(name=hyp_name)
    elif isinstance(hyp, FImpl):
        subgoal = Goal(
            formula=deepcopy(hyp.antecedent),
            context=current_goal.context
        )
        subgoals, assignment = _apply(current_goal, hyp_name, hyp.consequent, goals + [subgoal], idx + 1)
        return subgoals, PApp(fn=assignment, arg=PMetaVar(goal_id=subgoal.id))
    else:
        raise ValueError(f"Hypothesis '{hyp}' cannot be applied to the current goal '{current_goal.formula}'.")
