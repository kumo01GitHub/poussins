"""
"""
from copy import deepcopy
from typing import Optional, Any

from .constants import TacticSide
from ..ast import (
    EAnd,
    EOr,
    EExists,
    Expr,
    EVar,
    EApp,
    EEq,
    EImp,
    PMetaVar,
    PAndE,
    POrE,
    PExE,
    PVar,
)
from ..errors import TacticError
from ..kernel import Goal, ProofEngine


def _subst_term_in_term(term: Expr, var_name: str, replacement: Expr) -> Expr:
    match term:
        case EVar(name):
            return replacement if name == var_name else term
        case EApp(name, args):
            return EApp(name, tuple(_subst_term_in_term(arg, var_name, replacement) for arg in args))
        case _:
            return term


def _subst_term_in_expr(formula: Expr, var_name: str, replacement: Expr) -> Expr:
    match formula:
        case EApp(name, args):
            return EApp(name, tuple(_subst_term_in_term(arg, var_name, replacement) for arg in args))
        case EEq(left, right):
            return EEq(
                _subst_term_in_term(left, var_name, replacement),
                _subst_term_in_term(right, var_name, replacement),
            )
        case EImp(antecedent, consequent):
            return EImp(
                _subst_term_in_expr(antecedent, var_name, replacement),
                _subst_term_in_expr(consequent, var_name, replacement),
            )
        case EAnd(left, right):
            return EAnd(
                _subst_term_in_expr(left, var_name, replacement),
                _subst_term_in_expr(right, var_name, replacement),
            )
        case EOr(left, right):
            return EOr(
                _subst_term_in_expr(left, var_name, replacement),
                _subst_term_in_expr(right, var_name, replacement),
            )
        case EExists(bound_var, sort, body):
            if bound_var == var_name:
                return formula
            return EExists(bound_var, sort, _subst_term_in_expr(body, var_name, replacement))
        case _:
            return formula


def cases(engine: ProofEngine, hyp_name: str, pattern: Optional[tuple[Any, Any]] = None):
    """Apply the cases tactic to perform case analysis on a disjunction hypothesis."""
    current_goal = engine.state.current_goal
    if current_goal is None:
        raise TacticError("No active goal to apply cases tactic.")

    hyp = current_goal.context.get(hyp_name)
    if hyp is None:
        raise TacticError(f"Hypothesis '{hyp_name}' not found in the current context.")

    left_name, right_name = pattern if pattern is not None else (
        f"{hyp_name}{TacticSide.LEFT.symbol}",
        f"{hyp_name}{TacticSide.RIGHT.symbol}"
    )

    if isinstance(hyp, EAnd):
        subgoal = Goal(
            formula=deepcopy(current_goal.formula),
            context=current_goal.context
                .delete(hyp_name)
                .add({
                    left_name: hyp.left,
                    right_name: hyp.right
                })
        )
        engine.refine_goal(
            [subgoal],
            assignment=PAndE(
                conj_proof=PVar(name=hyp_name),
                left_hyp=left_name,
                right_hyp=right_name,
                case_proof=PMetaVar(goal_id=subgoal.id)
            )
        )
    elif isinstance(hyp, EOr):
        left_subgoal = Goal(
            formula = deepcopy(current_goal.formula),
            context = current_goal.context.delete(hyp_name).add({left_name: hyp.left})
        )
        right_subgoal = Goal(
            formula=deepcopy(current_goal.formula),
            context=current_goal.context.delete(hyp_name).add({right_name: hyp.right})
        )

        engine.refine_goal(
            [left_subgoal, right_subgoal],
            assignment=POrE(
                disj_proof=PVar(name=hyp_name),
                left_hyp=left_name,
                left_case=PMetaVar(goal_id=left_subgoal.id),
                right_hyp=right_name,
                right_case=PMetaVar(goal_id=right_subgoal.id)
            )
        )
    elif isinstance(hyp, EExists):
        witness_name, hyp_formula_name = pattern if pattern is not None else (
            f"{hyp_name}_w",
            f"{hyp_name}_h",
        )
        witness_term = EVar(witness_name)
        destructed_hyp_formula = _subst_term_in_expr(hyp.body, hyp.var, witness_term)

        subgoal = Goal(
            formula=deepcopy(current_goal.formula),
            context=current_goal.context
                .delete(hyp_name)
                .add_terms({witness_name: hyp.sort})
                .add({hyp_formula_name: destructed_hyp_formula}),
        )
        engine.refine_goal(
            [subgoal],
            assignment=PExE(
                exists_proof=PVar(name=hyp_name),
                witness_var=witness_name,
                hyp_var=hyp_formula_name,
                case_proof=PMetaVar(goal_id=subgoal.id),
            ),
        )
    else:
        raise TacticError(
            f"Hypothesis '{hyp_name}' is not a conjunction, disjunction, or existential and cannot be used with cases tactic."
        )
