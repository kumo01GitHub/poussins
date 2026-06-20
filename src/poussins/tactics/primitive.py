"""
Primitive tactics: intro, exact, apply.
"""
from copy import deepcopy

from ..ast import (
    Formula,
    FAnd,
    FImpl,
    ProofTerm,
    PMetaVar,
    PVar,
    PApp,
    PLam,
    PAndI,
)
from ..errors.tactic_error import TacticError
from ..kernel import ProofEngine, Goal


def intro(proof_engine: ProofEngine, hyp_name: str):
    """Introduce a new hypothesis."""
    current_goal = proof_engine.state.current_goal
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
        raise TacticError("No active goal to apply exact tactic.")

    hyp = current_goal.context.get(hyp_name)
    if hyp is None:
        raise TacticError(f"Hypothesis '{hyp_name}' not found in the current context.")
    elif hyp != current_goal.formula:
        raise TacticError(f"Hypothesis '{hyp_name}' does not match the current goal formula.")

    proof_engine.close_goal(PVar(name=hyp_name))


def apply(proof_engine: ProofEngine, hyp_name: str):
    current_goal = proof_engine.state.current_goal
    if current_goal is None:
        raise TacticError("No active goal to apply apply tactic.")

    hyp = current_goal.context.get(hyp_name)
    if hyp is None:
        raise TacticError(f"Hypothesis '{hyp_name}' not found in the current context.")
    elif hyp == current_goal.formula:
        exact(proof_engine, hyp_name)
        return
    elif not isinstance(hyp, FImpl):
        raise TacticError(f"Hypothesis '{hyp_name}' is not an implication and cannot be applied.")

    subgoals: list[Goal] = []
    assignment: ProofTerm = PVar(name=hyp_name)
    current_formula: Formula = hyp
    while isinstance(current_formula, FImpl):
        subgoal = Goal(
            formula=deepcopy(current_formula.antecedent),
            context=current_goal.context
        )
        subgoals.append(subgoal)
        assignment = PApp(fn=assignment, arg=PMetaVar(goal_id=subgoal.id))
        current_formula = current_formula.consequent

    if current_goal.formula != current_formula:
        raise TacticError(f"Hypothesis '{hyp}' cannot be applied to the current goal '{current_goal.formula}'.")

    proof_engine.refine_goal(subgoals=subgoals, assignment=assignment)


def split(proof_engine: ProofEngine):
    """Split a conjunction goal into two sub-goals."""
    current_goal = proof_engine.state.current_goal
    if current_goal is None:
        raise TacticError("No active goal to apply split tactic.")
    elif not isinstance(current_goal.formula, FAnd):
        raise TacticError("Split tactic can only be applied to conjunctions.")

    left_subgoal = Goal(
        formula=deepcopy(current_goal.formula.left),
        context=current_goal.context
    )
    right_subgoal = Goal(
        formula=deepcopy(current_goal.formula.right),
        context=current_goal.context
    )
    proof_engine.refine_goal(
        [left_subgoal, right_subgoal],
        assignment=PAndI(
            left=PMetaVar(goal_id=left_subgoal.id),
            right=PMetaVar(goal_id=right_subgoal.id)
        )
    )
