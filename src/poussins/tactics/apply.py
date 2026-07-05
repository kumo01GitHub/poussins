"""
Apply tactic: applies a hypothesis or a theorem to the current goal, generating subgoals for the premises of the hypothesis/theorem.
"""
from copy import deepcopy
from typing import Optional

from ..ast import Expr, EImp, ProofTerm, PApp, PMetaVar, PVar
from ..errors import TacticError
from ..framework import Environment
from ..kernel import ProofEngine, Goal


def apply(engine: ProofEngine, hyp_name: str, env: Optional[Environment]):
    current_goal = engine.state.current_goal
    if current_goal is None:
        raise TacticError("No active goal to apply apply tactic.")

    hyp = current_goal.context.get(hyp_name)
    if hyp is not None and hyp == current_goal.formula:
        engine.close_goal(PVar(name=hyp_name))
        return
    elif hyp is None:
        if env is None:
            env = Environment()
        declaration = env.get(hyp_name)
        if (
            declaration is not None
            and declaration.has_statement
            and declaration.statement == current_goal.formula
            and declaration.assignment is not None
        ):
            engine.close_goal(declaration.assignment)
            return
        elif declaration is not None and declaration.has_statement:
            hyp = declaration.statement

    if hyp is None:
        raise TacticError(f"Hypothesis '{hyp_name}' not found in the current context.")
    elif not isinstance(hyp, EImp):
        raise TacticError(f"Hypothesis '{hyp_name}' is not an implication and cannot be applied.")

    subgoals: list[Goal] = []
    assignment: ProofTerm = PVar(name=hyp_name)
    current_formula: Expr = hyp
    while isinstance(current_formula, EImp):
        subgoal = Goal(
            formula=deepcopy(current_formula.antecedent),
            context=current_goal.context
        )
        subgoals.append(subgoal)
        assignment = PApp(fn=assignment, arg=PMetaVar(goal_id=subgoal.id))
        current_formula = current_formula.consequent

    if current_goal.formula != current_formula:
        raise TacticError(f"Hypothesis '{hyp}' cannot be applied to the current goal '{current_goal.formula}'.")

    engine.refine_goal(subgoals=subgoals, assignment=assignment)
