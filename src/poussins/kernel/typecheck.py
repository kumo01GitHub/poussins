"""
Stateless kernel routines for inference, checking, and unification.
"""
from __future__ import annotations

from collections.abc import Mapping

from .proof_state import MetaVar
from ..ast import (
    Expr, ESort, EVar, EConst, EPi, ELam, EApp, EMatch, EMetaVar,
    UnivLevelZero, UnivLevelSucc, UnivLevelIMax,
    collect_free_vars, substitute_metavar, substitute_expr_var
)
from ..errors import KernelTypeError


Definitions = Mapping[str, Expr | None] | None


def instantiate_meta(expr: Expr, metavars: dict[str, MetaVar]) -> Expr:
    """
    Instantiate assigned metavariables in an expression.
    """
    current = expr
    for goal_id, m in metavars.items():
        if m.is_assigned:
            current = substitute_metavar(current, goal_id, m.assignment)
    return current


def whnf(
    expr: Expr,
    metavars: dict[str, MetaVar],
    definitions: Definitions = None,
    unfolding: frozenset[str] = frozenset(),
) -> Expr:
    """
    Reduce an expression to weak head normal form.
    """
    expr = instantiate_meta(expr, metavars)

    match expr:
        case EConst(name, _):
            if definitions is not None and name in definitions and definitions[name] is not None and name not in unfolding:
                return whnf(definitions[name], metavars, definitions, unfolding | {name})
            return expr
        case EApp(fn, arg):
            fn_whnf = whnf(fn, metavars, definitions, unfolding)
            if isinstance(fn_whnf, ELam):
                new_expr = substitute_expr_var(fn_whnf.body, fn_whnf.var, arg)
                return whnf(new_expr, metavars, definitions, unfolding)
            return EApp(fn_whnf, arg)
        case _:
            return expr


def instantiate(expr: Expr, metavars: dict[str, MetaVar]) -> Expr:
    """
    Recursively replace all assigned metavariables in an expression.
    """
    current = expr
    while True:
        next_term = instantiate_meta(current, metavars)
        if next_term == current:
            break
        current = next_term
    return current


def is_universe_leq(level_left: object, level_right: object) -> bool:
    """
    Return True when the left universe level is below or equal to the right.
    """
    if level_left == level_right:
        return True

    match (level_left, level_right):
        case (UnivLevelZero(), UnivLevelSucc(_)):
            return True
        case (UnivLevelSucc(pred_left), UnivLevelSucc(pred_right)):
            return is_universe_leq(pred_left, pred_right)
        case (UnivLevelZero(), UnivLevelIMax(left, right)):
            return is_universe_leq(level_left, left) or is_universe_leq(level_left, right)
        case (UnivLevelSucc(_), UnivLevelIMax(left, right)):
            return is_universe_leq(level_left, left) or is_universe_leq(level_left, right)
        case _:
            return False


def infer_type(
    expr: Expr,
    context: dict[str, Expr],
    metavars: dict[str, MetaVar],
    definitions: Definitions = None,
) -> Expr:
    """
    Infer the type of an expression.
    """
    expr = instantiate_meta(expr, metavars)

    match expr:
        case EMetaVar(goal_id):
            if goal_id not in metavars:
                raise KernelTypeError(f"Unknown meta-variable ?{goal_id}")
            return metavars[goal_id].statement

        case ESort(level):
            return ESort(UnivLevelSucc(level))

        case EVar(name) | EConst(name, _):
            t = context.get(name)
            if t is None:
                raise KernelTypeError(f"Unknown identifier '{name}' (neither local variable nor verified constant).")
            return t

        case EPi(var, domain, body):
            sort_a = infer_type(domain, context, metavars, definitions)
            sort_a_whnf = whnf(sort_a, metavars, definitions)
            if not isinstance(sort_a_whnf, ESort):
                raise KernelTypeError("The domain of a dependent product must be a Sort.")

            sort_b = infer_type(body, context | {var: domain}, metavars, definitions)
            sort_b_whnf = whnf(sort_b, metavars, definitions)
            if not isinstance(sort_b_whnf, ESort):
                raise KernelTypeError("The body of a dependent product must be a Sort.")

            return ESort(UnivLevelIMax(sort_a_whnf.level, sort_b_whnf.level))

        case ELam(var, domain, body):
            extended_context = context | {var: domain}
            body_type = infer_type(body, extended_context, metavars, definitions)

            infer_type(EPi(var, domain, body_type), context, metavars, definitions)
            return EPi(var, domain, body_type)

        case EApp(fn, arg):
            fn_type = infer_type(fn, context, metavars, definitions)
            arg_type = infer_type(arg, context, metavars, definitions)

            fn_type_whnf = whnf(fn_type, metavars, definitions)

            if not isinstance(fn_type_whnf, EPi):
                raise KernelTypeError(f"Expected function type (EPi), but found: {fn_type_whnf}")

            expected_domain = whnf(fn_type_whnf.domain, metavars, definitions)
            actual_arg_type = whnf(arg_type, metavars, definitions)
            if not is_def_eq(expected_domain, actual_arg_type, context, metavars, definitions):
                raise KernelTypeError(f"Argument type mismatch. Expected: {expected_domain}, Found: {actual_arg_type}")

            return substitute_expr_var(fn_type_whnf.body, fn_type_whnf.var, arg)

        case EMatch(_, discriminee, motive, _):
            return EApp(motive, discriminee)

        case _:
            raise NotImplementedError(f"Unknown expression node: {expr}")


def check_type(
    expr: Expr,
    expected_type: Expr,
    context: dict[str, Expr],
    metavars: dict[str, MetaVar],
    definitions: Definitions = None,
) -> bool:
    """
    Return True when the expression checks against the expected type.
    """
    try:
        inferred = infer_type(expr, context, metavars, definitions)
        if is_def_eq(inferred, expected_type, context, metavars, definitions):
            return True
        if isinstance(inferred, ESort) and isinstance(expected_type, ESort):
            return is_universe_leq(inferred.level, expected_type.level)
        return False
    except KernelTypeError:
        return False


def is_alpha_eq(t1: Expr, t2: Expr, bvars1: list[str] = [], bvars2: list[str] = []) -> bool:
    """
    Return True when two expressions are alpha-equivalent.
    """
    if type(t1) is not type(t2):
        return False

    match (t1, t2):
        case (EVar(n1), EVar(n2)):
            if n1 in bvars1 or n2 in bvars2:
                try:
                    return bvars1.index(n1) == bvars2.index(n2)
                except ValueError:
                    return False
            return n1 == n2

        case (ESort(l1), ESort(l2)):
            return l1 == l2

        case (EConst(n1, lv1), EConst(n2, lv2)):
            return n1 == n2 and lv1 == lv2

        case (EMetaVar(g1), EMetaVar(g2)):
            return g1 == g2

        case (EPi(v1, d1, b1), EPi(v2, d2, b2)) | (ELam(v1, d1, b1), ELam(v2, d2, b2)):
            if not is_alpha_eq(d1, d2, bvars1, bvars2):
                return False
            return is_alpha_eq(b1, b2, [v1] + bvars1, [v2] + bvars2)

        case (EApp(f1, a1), EApp(f2, a2)):
            return is_alpha_eq(f1, f2, bvars1, bvars2) and is_alpha_eq(a1, a2, bvars1, bvars2)

        case (EMatch(i1, d1, m1, c1), EMatch(i2, d2, m2, c2)):
            if i1 != i2 or not is_alpha_eq(d1, d2, bvars1, bvars2) or not is_alpha_eq(m1, m2, bvars1, bvars2):
                return False
            if len(c1) != len(c2):
                return False
            return all(is_alpha_eq(b1, b2, bvars1, bvars2) for b1, b2 in zip(c1, c2))

        case _:
            return False


def is_def_eq(
    t1: Expr,
    t2: Expr,
    context: dict[str, Expr],
    metavars: dict[str, MetaVar],
    definitions: Definitions = None,
) -> bool:
    """
    Return True when two expressions are definitionally equal.
    """
    t1 = instantiate(t1, metavars)
    t2 = instantiate(t2, metavars)

    if is_alpha_eq(t1, t2):
        return True

    t1_whnf = whnf(t1, metavars, definitions)
    t2_whnf = whnf(t2, metavars, definitions)

    if t1_whnf != t1 or t2_whnf != t2:
        if is_alpha_eq(t1_whnf, t2_whnf):
            return True

    if isinstance(t1_whnf, ELam) and isinstance(t2_whnf, EVar):
        if not isinstance(t1_whnf.body, EApp):
            return False
        if not isinstance(t1_whnf.body.arg, EVar):
            return False
        if t1_whnf.body.arg.name != t1_whnf.var:
            return False
        if t1_whnf.body.arg.name in collect_free_vars(t1_whnf.body.fn):
            return False
        return is_def_eq(t1_whnf.body.fn, t2_whnf, context, metavars, definitions)

    if isinstance(t1_whnf, EVar) and isinstance(t2_whnf, ELam):
        if not isinstance(t2_whnf.body, EApp):
            return False
        if not isinstance(t2_whnf.body.arg, EVar):
            return False
        if t2_whnf.body.arg.name != t2_whnf.var:
            return False
        if t2_whnf.body.arg.name in collect_free_vars(t2_whnf.body.fn):
            return False
        return is_def_eq(t1_whnf, t2_whnf.body.fn, context, metavars, definitions)

    if type(t1_whnf) is not type(t2_whnf):
        return False

    match (t1_whnf, t2_whnf):
        case (ESort(level1), ESort(level2)):
            return level1 == level2

        case (EApp(f1, a1), EApp(f2, a2)):
            return (
                is_def_eq(f1, f2, context, metavars, definitions) and
                is_def_eq(a1, a2, context, metavars, definitions)
            )

        case (EPi(v1, d1, b1), EPi(v2, d2, b2)) | (ELam(v1, d1, b1), ELam(v2, d2, b2)):
            if not is_def_eq(d1, d2, context, metavars, definitions):
                return False

            if v1 != v2:
                b2 = substitute_expr_var(b2, var_name=v2, replacement=EVar(v1))

            return is_def_eq(b1, b2, context | {v1: d1}, metavars, definitions)

        case (EMatch(i1, d1, m1, c1), EMatch(i2, d2, m2, c2)):
            if i1 != i2:
                return False
            if not is_def_eq(d1, d2, context, metavars, definitions):
                return False
            if not is_def_eq(m1, m2, context, metavars, definitions):
                return False
            if len(c1) != len(c2):
                return False
            return all(is_def_eq(b1, b2, context, metavars, definitions) for b1, b2 in zip(c1, c2))

        case _:
            return False


def unify(
    t1: Expr,
    t2: Expr,
    context: dict[str, Expr],
    metavars: dict[str, MetaVar],
    definitions: Definitions = None,
) -> dict[str, MetaVar]:
    """
    Unify two expressions and return updated metavariable assignments.
    """
    t1 = instantiate(t1, metavars)
    t2 = instantiate(t2, metavars)

    if is_alpha_eq(t1, t2):
        return metavars

    if isinstance(t1, EMetaVar):
        mvar_id = t1.goal_id
        if mvar_id in metavars and not metavars[mvar_id].is_assigned:
            return metavars | {mvar_id: MetaVar(statement=metavars[mvar_id].statement, assignment=t2)}

    if isinstance(t2, EMetaVar):
        mvar_id = t2.goal_id
        if mvar_id in metavars and not metavars[mvar_id].is_assigned:
            return metavars | {mvar_id: MetaVar(statement=metavars[mvar_id].statement, assignment=t1)}

    t1_whnf = whnf(t1, metavars, definitions)
    t2_whnf = whnf(t2, metavars, definitions)

    if t1_whnf != t1 or t2_whnf != t2:
        if is_alpha_eq(t1_whnf, t2_whnf):
            return metavars
        if isinstance(t1_whnf, EMetaVar) or isinstance(t2_whnf, EMetaVar):
            return unify(t1_whnf, t2_whnf, context, metavars, definitions)

    if type(t1_whnf) is not type(t2_whnf):
        raise KernelTypeError(f"Unification failed: type mismatch between {t1_whnf} and {t2_whnf}")

    match (t1_whnf, t2_whnf):
        case (EApp(f1, a1), EApp(f2, a2)):
            current_metavars = unify(f1, f2, context, metavars, definitions)
            return unify(a1, a2, context, current_metavars, definitions)

        case (EPi(v1, d1, b1), EPi(v2, d2, b2)) | (ELam(v1, d1, b1), ELam(v2, d2, b2)):
            current_metavars = unify(d1, d2, context, metavars, definitions)
            if v1 != v2:
                b2 = substitute_expr_var(b2, var_name=v2, replacement=EVar(v1))
            return unify(b1, b2, context | {v1: d1}, current_metavars, definitions)

        case (EMatch(i1, d1, m1, c1), EMatch(i2, d2, m2, c2)):
            if i1 != i2:
                raise KernelTypeError("Unification failed: match inductive type mismatch")
            current_metavars = unify(d1, d2, context, metavars, definitions)
            current_metavars = unify(m1, m2, context, current_metavars, definitions)
            if len(c1) != len(c2):
                raise KernelTypeError("Unification failed: match branch length mismatch")
            for b1, b2 in zip(c1, c2):
                current_metavars = unify(b1, b2, context, current_metavars, definitions)
            return current_metavars

        case _:
            raise KernelTypeError(f"Unification failed: expressions are structurally distinct: {t1_whnf} vs {t2_whnf}")
