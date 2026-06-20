"""
Primitive tactics: intro, exact, apply.
"""
from copy import deepcopy
from typing import Optional

from ..ast import (
    Formula,
    FAnd,
    FOr,
    FImpl,
    FTrue,
    ProofTerm,
    PMetaVar,
    PVar,
    PApp,
    PLam,
    PAndI,
    PTrueI,
    POrIL,
    POrIR,
)
from ..errors.tactic_error import TacticError
from ..framework import Environment
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


def exact(proof_engine: ProofEngine, hyp_name: str, env: Optional[Environment]):
    """Close the current goal with a hypothesis."""
    current_goal = proof_engine.state.current_goal
    if current_goal is None:
        raise TacticError("No active goal to apply exact tactic.")

    hyp = current_goal.context.get(hyp_name)
    if hyp is None and env is not None:
        declaration = env.get(hyp_name)
        if declaration is not None:
            hyp = declaration.statement

    if hyp is None:
        raise TacticError(f"Hypothesis '{hyp_name}' not found in the current context.")
    elif hyp != current_goal.formula:
        raise TacticError(f"Hypothesis '{hyp_name}' does not match the current goal formula.")

    proof_engine.close_goal(PVar(name=hyp_name))


def apply(proof_engine: ProofEngine, hyp_name: str, env: Optional[Environment]):
    current_goal = proof_engine.state.current_goal
    if current_goal is None:
        raise TacticError("No active goal to apply apply tactic.")

    hyp = current_goal.context.get(hyp_name)
    if hyp is None and env is not None:
        declaration = env.get(hyp_name)
        if declaration is not None:
            hyp = declaration.statement

    if hyp is None:
        raise TacticError(f"Hypothesis '{hyp_name}' not found in the current context.")
    elif hyp == current_goal.formula:
        exact(proof_engine, hyp_name, env)
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


def constructor(proof_engine: ProofEngine, idx: int = 1):
    """Apply the constructor tactic to split a conjunction goal into subgoals."""
    current_goal = proof_engine.state.current_goal
    if current_goal is None:
        raise TacticError("No active goal to apply constructor tactic.")

    if isinstance(current_goal.formula, FTrue):
        proof_engine.close_goal(PTrueI)
    elif isinstance(current_goal.formula, FAnd):
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
    elif isinstance(current_goal.formula, FOr):
        if idx == 1:
            subgoal = Goal(
                formula=deepcopy(current_goal.formula.left),
                context=current_goal.context
            )
            proof_engine.refine_goal(
                [subgoal],
                assignment=POrIL(
                    proof=PMetaVar(goal_id=subgoal.id),
                    other_disjunct=deepcopy(current_goal.formula.right)
                )
            )
        elif idx == 2:
            subgoal = Goal(
                formula=deepcopy(current_goal.formula.right),
                context=current_goal.context
            )
            proof_engine.refine_goal(
                [subgoal],
                assignment=POrIR(
                    other_disjunct=deepcopy(current_goal.formula.left),
                    proof=PMetaVar(goal_id=subgoal.id)
                )
            )
        else:
            raise TacticError("Constructor tactic for disjunction requires an index of 1 or 2.")
    else:
        raise TacticError("Constructor tactic can only be applied to conjunction or disjunction goals.")
