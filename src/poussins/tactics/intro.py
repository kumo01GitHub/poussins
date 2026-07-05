"""
Intro tactic: introduces a new hypothesis for an implication goal, generating a subgoal for the consequent."""
from copy import deepcopy

from ..ast import EImp, EForall, Expr, EVar, EApp, EEq, EPred, EAnd, EOr, EExists, PLam, PMetaVar, PForallI
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
        case EPred(name, args):
            return EPred(name, tuple(_subst_term_in_term(arg, var_name, replacement) for arg in args))
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
        case EForall(bound_var, sort, body):
            if bound_var == var_name:
                return formula
            return EForall(bound_var, sort, _subst_term_in_expr(body, var_name, replacement))
        case EExists(bound_var, sort, body):
            if bound_var == var_name:
                return formula
            return EExists(bound_var, sort, _subst_term_in_expr(body, var_name, replacement))
        case _:
            return formula


def intro(engine: ProofEngine, hyp_name: str):
    """Introduce a new hypothesis."""
    current_goal = engine.state.current_goal
    if current_goal is None:
        raise TacticError("No active goal to apply intro tactic.")
    elif isinstance(current_goal.formula, EImp):
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
    elif isinstance(current_goal.formula, EForall):
        witness_var = EVar(hyp_name)
        subgoal = Goal(
            formula=_subst_term_in_expr(
                current_goal.formula.body,
                current_goal.formula.var,
                witness_var,
            ),
            context=current_goal.context.add_terms({hyp_name: current_goal.formula.sort}),
        )
        engine.refine_goal(
            [subgoal],
            assignment=PForallI(
                var=hyp_name,
                sort=deepcopy(current_goal.formula.sort),
                body=PMetaVar(goal_id=subgoal.id),
            ),
        )
    else:
        raise TacticError("Intro tactic can only be applied to implications or universals.")


def intros(engine: ProofEngine, hyp_names: list[str]):
    for hyp_name in hyp_names:
        intro(engine, hyp_name)
