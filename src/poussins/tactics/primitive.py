"""
"""

from copy import deepcopy

from ..ast.proof_terms import PLam, ProofTerm
from ..errors.tactic_error import TacticError

from ..kernel.proof_engine import ProofEngine
from ..kernel.goal import Goal
from ..ast import Formula, FImpl, PMetaVar, PVar, PApp


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
