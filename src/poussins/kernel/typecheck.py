"""Kernel-level type checking and inference functions for the proof system."""
from __future__ import annotations

from ..ast import (
    EApp,
    EBVar,
    EConst,
    EFVar,
    ELam,
    EMetaVar,
    EPi,
    ESort,
    Expr,
    UnivLevelIMax,
    UnivLevelSucc,
    collect_metavar_ids,
    instantiate_binder,
    pi,
    shift_bvars,
)
from ..environment import Environment
from ..errors import KernelTypeError
from .equality import is_def_eq
from .eval import instantiate_metavar, whnf
from .proof_state import MetaVar
from .univ import instantiate_univ, is_universe_leq


def _infer_metavar(expr: EMetaVar, metavars: dict[str, MetaVar]) -> Expr:
    """Infer the type of a metavariable expression."""
    if expr.goal_id not in metavars:
        raise KernelTypeError(f"Unknown meta-variable ?{expr.goal_id}")
    return metavars[expr.goal_id].statement


def _infer_sort(expr: ESort) -> Expr:
    """Infer the type of a sort expression."""
    return ESort(UnivLevelSucc(expr.level))


def _infer_fvar(expr: EFVar, context: dict[str, Expr]) -> Expr:
    """Infer the type of a free variable expression."""
    inferred = context.get(expr.name)
    if inferred is None:
        raise KernelTypeError(f"Unknown local variable '{expr.name}'.")
    return inferred


def _infer_bvar(expr: EBVar, bound_context: list[Expr]) -> Expr:
    """Infer the type of a bound variable expression."""
    if expr.index < 0 or expr.index >= len(bound_context):
        raise KernelTypeError(f"Unknown bound variable index '{expr.index}'.")
    return bound_context[expr.index]


def _infer_const(
    expr: EConst,
    context: dict[str, Expr],
    env: Environment | None,
) -> Expr:
    """Infer the type of a constant expression."""
    if env is not None:
        decl = env.get(expr.name)
        if decl is not None:
            inferred = decl.type
            level_params = decl.level_params
            if expr.levels and level_params:
                if len(expr.levels) != len(level_params):
                    raise KernelTypeError(
                        f"Incorrect number of universe levels for {expr.name}"
                    )
                inferred = instantiate_univ(
                    inferred,
                    dict(zip(level_params, expr.levels, strict=False)),
                )
            return inferred

    inferred = context.get(expr.name)
    if inferred is None:
        raise KernelTypeError(f"Unknown constant '{expr.name}'.")
    return inferred


def _infer_pi(
    expr: EPi,
    context: dict[str, Expr],
    metavars: dict[str, MetaVar],
    env: Environment | None,
    bound_context: list[Expr],
) -> Expr:
    """Infer the type of a dependent product expression."""
    sort_a = _infer_type(expr.domain, context, metavars, env, bound_context)
    sort_a_whnf = whnf(sort_a, metavars, env)
    if not isinstance(sort_a_whnf, ESort):
        raise KernelTypeError("The domain of a dependent product must be a Sort.")

    extended_bound_context = [shift_bvars(expr.domain, 1)] + [
        shift_bvars(bound_type, 1) for bound_type in bound_context
    ]
    sort_b = _infer_type(
        expr.body,
        context | {expr.var: expr.domain},
        metavars,
        env,
        extended_bound_context,
    )
    sort_b_whnf = whnf(sort_b, metavars, env)
    if not isinstance(sort_b_whnf, ESort):
        raise KernelTypeError("The body of a dependent product must be a Sort.")

    return ESort(UnivLevelIMax(sort_a_whnf.level, sort_b_whnf.level))


def _infer_lam(
    expr: ELam,
    context: dict[str, Expr],
    metavars: dict[str, MetaVar],
    env: Environment | None,
    bound_context: list[Expr],
) -> Expr:
    """Infer the type of a lambda expression."""
    domain_sort = _infer_type(expr.domain, context, metavars, env, bound_context)
    if not isinstance(whnf(domain_sort, metavars, env), ESort):
        raise KernelTypeError("The domain of a lambda must be a Sort.")

    extended_context = context | {expr.var: expr.domain}
    opened_body = instantiate_binder(expr.body, EFVar(expr.var))
    body_type = _infer_type(
        opened_body,
        extended_context,
        metavars,
        env,
        bound_context,
    )
    return pi(((expr.var, expr.domain),), body_type)


def _infer_app(
    expr: EApp,
    context: dict[str, Expr],
    metavars: dict[str, MetaVar],
    env: Environment | None,
    bound_context: list[Expr],
) -> Expr:
    """Infer the type of an application expression."""
    fn_type = _infer_type(expr.fn, context, metavars, env, bound_context)
    arg_type = _infer_type(expr.arg, context, metavars, env, bound_context)
    fn_type_whnf = whnf(fn_type, metavars, env)
    if not isinstance(fn_type_whnf, EPi):
        raise KernelTypeError(
            f"Expected function type (EPi), but found: {fn_type_whnf}"
        )

    expected_domain = whnf(fn_type_whnf.domain, metavars, env)
    actual_arg_type = whnf(arg_type, metavars, env)
    if not is_def_eq(expected_domain, actual_arg_type, context, metavars, env):
        raise KernelTypeError(
            "Argument type mismatch. "
            + f"Expected: {expected_domain}, Found: {actual_arg_type}"
        )
    return instantiate_binder(fn_type_whnf.body, expr.arg)


def _infer_type(
    expr: Expr,
    context: dict[str, Expr],
    metavars: dict[str, MetaVar],
    env: Environment | None,
    bound_context: list[Expr],
) -> Expr:
    """Infer the type of an expression."""
    expr = instantiate_metavar(expr, metavars)

    match expr:
        case EMetaVar():
            return _infer_metavar(expr, metavars)
        case ESort():
            return _infer_sort(expr)
        case EFVar():
            return _infer_fvar(expr, context)
        case EBVar():
            return _infer_bvar(expr, bound_context)
        case EConst():
            return _infer_const(expr, context, env)
        case EPi():
            return _infer_pi(expr, context, metavars, env, bound_context)
        case ELam():
            return _infer_lam(expr, context, metavars, env, bound_context)
        case EApp():
            return _infer_app(expr, context, metavars, env, bound_context)


def infer_type(
    expr: Expr,
    context: dict[str, Expr],
    metavars: dict[str, MetaVar],
    env: Environment | None = None,
) -> Expr:
    """Infer the type of an expression."""
    return _infer_type(expr, context, metavars, env, [])


def check_type(
    expr: Expr,
    expected_type: Expr,
    context: dict[str, Expr],
    metavars: dict[str, MetaVar],
    env: Environment | None = None,
) -> bool:
    """Return True when the expression checks against the expected type."""
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
    """Infer the expected types for each metavariable in an expression."""
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
                    if isinstance(fn_type_whnf, (EPi, ELam)):
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
