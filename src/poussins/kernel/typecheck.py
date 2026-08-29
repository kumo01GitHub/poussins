"""
Kernel-level type checking and inference functions for the proof system.
"""
from __future__ import annotations

from .equality import is_def_eq
from .eval import instantiate_metavar, whnf
from .proof_state import MetaVar
from .univ import is_universe_leq, instantiate_univ
from ..ast import (
    Expr, ESort, EVar, EConst, EPi, ELam, EApp, EMatch, EMetaVar,
    UnivLevelSucc, UnivLevelIMax,
    substitute_expr_var, collect_metavar_ids
)
from ..environment import Environment
from ..errors import KernelTypeError


def infer_type(
    expr: Expr,
    context: dict[str, Expr],
    metavars: dict[str, MetaVar],
    env: Environment | None = None,
) -> Expr:
    """
    Infer the type of an expression.
    """
    expr = instantiate_metavar(expr, metavars)

    match expr:
        case EMetaVar(goal_id):
            if goal_id not in metavars:
                raise KernelTypeError(f"Unknown meta-variable ?{goal_id}")
            return metavars[goal_id].statement
        case ESort(level):
            return ESort(UnivLevelSucc(level))
        case EVar(name):
            t = context.get(name)
            if t is None:
                raise KernelTypeError(f"Unknown local variable '{name}'.")
            return t
        case EConst(name, levels):
            if env is not None:
                decl = env.get(name)
                if decl is not None:
                    t = decl.type
                    level_params = getattr(decl, "level_params", None)
                    if levels and level_params:
                        if len(levels) != len(level_params):
                            raise KernelTypeError(f"Incorrect number of universe levels for {name}")
                        level_subst = dict(zip(level_params, levels))
                        t = instantiate_univ(t, level_subst)
                    return t
            t = context.get(name)
            if t is None:
                raise KernelTypeError(f"Unknown constant '{name}'.")
            return t
        case EPi(var, domain, body):
            sort_a = infer_type(domain, context, metavars, env)
            sort_a_whnf = whnf(sort_a, metavars, env)
            if not isinstance(sort_a_whnf, ESort):
                raise KernelTypeError("The domain of a dependent product must be a Sort.")
            sort_b = infer_type(body, context | {var: domain}, metavars, env)
            sort_b_whnf = whnf(sort_b, metavars, env)
            if not isinstance(sort_b_whnf, ESort):
                raise KernelTypeError("The body of a dependent product must be a Sort.")
            return ESort(UnivLevelIMax(sort_a_whnf.level, sort_b_whnf.level))
        case ELam(var, domain, body):
            extended_context = context | {var: domain}
            body_type = infer_type(body, extended_context, metavars, env)
            _ = infer_type(EPi(var, domain, body_type), context, metavars, env)
            return EPi(var, domain, body_type)
        case EApp(fn, arg):
            fn_type = infer_type(fn, context, metavars, env)
            arg_type = infer_type(arg, context, metavars, env)
            fn_type_whnf = whnf(fn_type, metavars, env)
            if not isinstance(fn_type_whnf, EPi):
                raise KernelTypeError(f"Expected function type (EPi), but found: {fn_type_whnf}")
            expected_domain = whnf(fn_type_whnf.domain, metavars, env)
            actual_arg_type = whnf(arg_type, metavars, env)
            if not is_def_eq(expected_domain, actual_arg_type, context, metavars, env):
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
    env: Environment | None = None,
) -> bool:
    """
    Return True when the expression checks against the expected type.
    """
    try:
        inferred = infer_type(expr, context, metavars, env)
        if is_def_eq(inferred, expected_type, context, metavars, env):
            return True
        if isinstance(inferred, ESort) and isinstance(expected_type, ESort):
            return is_universe_leq(inferred.level, expected_type.level)
        return False
    except KernelTypeError:
        return False


def infer_metavar_types(
    expr: Expr,
    expected_type: Expr,
    context: dict[str, Expr],
    metavars: dict[str, MetaVar],
    env: Environment | None = None,
) -> dict[str, Expr]:
    """
    Infer the expected types for each metavariable in an expression.
    """
    meta_types: dict[str, Expr] = {}

    def _walk(e: Expr, expected: Expr, ctx: dict[str, Expr]) -> None:
        e_whnf = whnf(e, metavars, env)
        match e_whnf:
            case EMetaVar(mvar_id):
                meta_types[mvar_id] = expected
            case EApp(fn, arg):
                try:
                    fn_type = infer_type(fn, ctx, metavars, env)
                    fn_type_whnf = whnf(fn_type, metavars, env)
                    if hasattr(fn_type_whnf, "domain"):
                        _walk(arg, fn_type_whnf.domain, ctx)
                        _walk(fn, fn_type, ctx)
                except KernelTypeError:
                    pass
            case _:
                pass

    _walk(expr, expected_type, context)
    for m_id in collect_metavar_ids(expr):
        if m_id not in meta_types:
            meta_types[m_id] = expected_type
    return meta_types
