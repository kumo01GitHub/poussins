"""Kernel-level type checking and inference functions for the proof system."""
from __future__ import annotations

from ..ast import (
    EApp,
    EConst,
    ELam,
    EMatch,
    EMetaVar,
    EPi,
    ESort,
    EVar,
    Expr,
    UnivLevelIMax,
    UnivLevelParam,
    UnivLevelSucc,
    build_app_chain,
    collect_metavar_ids,
    flatten_app_chain,
    substitute_expr_var,
)
from ..environment import ConstructorDeclaration, Environment, InductiveDeclaration
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


def _infer_var(expr: EVar, context: dict[str, Expr]) -> Expr:
    """Infer the type of a variable expression."""
    inferred = context.get(expr.name)
    if inferred is None:
        raise KernelTypeError(f"Unknown local variable '{expr.name}'.")
    return inferred


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
) -> Expr:
    """Infer the type of a dependent product expression."""
    sort_a = infer_type(expr.domain, context, metavars, env)
    sort_a_whnf = whnf(sort_a, metavars, env)
    if not isinstance(sort_a_whnf, ESort):
        raise KernelTypeError("The domain of a dependent product must be a Sort.")

    sort_b = infer_type(expr.body, context | {expr.var: expr.domain}, metavars, env)
    sort_b_whnf = whnf(sort_b, metavars, env)
    if not isinstance(sort_b_whnf, ESort):
        raise KernelTypeError("The body of a dependent product must be a Sort.")

    return ESort(UnivLevelIMax(sort_a_whnf.level, sort_b_whnf.level))


def _infer_lam(
    expr: ELam,
    context: dict[str, Expr],
    metavars: dict[str, MetaVar],
    env: Environment | None,
) -> Expr:
    """Infer the type of a lambda expression."""
    extended_context = context | {expr.var: expr.domain}
    body_type = infer_type(expr.body, extended_context, metavars, env)
    _ = infer_type(EPi(expr.var, expr.domain, body_type), context, metavars, env)
    return EPi(expr.var, expr.domain, body_type)


def _infer_app(
    expr: EApp,
    context: dict[str, Expr],
    metavars: dict[str, MetaVar],
    env: Environment | None,
) -> Expr:
    """Infer the type of an application expression."""
    fn_type = infer_type(expr.fn, context, metavars, env)
    arg_type = infer_type(expr.arg, context, metavars, env)
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
    return substitute_expr_var(fn_type_whnf.body, fn_type_whnf.var, expr.arg)


def _infer_match(
    expr: EMatch,
    context: dict[str, Expr],
    metavars: dict[str, MetaVar],
    env: Environment | None,
) -> Expr:
    """Infer the type of a match expression and validate branch typings."""
    if env is None:
        raise KernelTypeError("Match typing requires an environment with declarations.")

    discriminee_type = whnf(
        infer_type(expr.discriminee, context, metavars, env),
        metavars,
        env,
    )
    discriminee_head, _ = flatten_app_chain(discriminee_type)
    if not isinstance(discriminee_head, EConst):
        raise KernelTypeError("Match discriminee must have an inductive type head.")
    if discriminee_head.name != expr.inductive_name:
        raise KernelTypeError(
            "Match discriminee type mismatch. "
            + f"Expected '{expr.inductive_name}', found '{discriminee_head.name}'."
        )

    inductive_decl = env.get(expr.inductive_name)
    if not isinstance(inductive_decl, InductiveDeclaration):
        raise KernelTypeError(f"'{expr.inductive_name}' is not an inductive type.")

    constructor_names = inductive_decl.constructor_names
    if len(expr.cases) != len(constructor_names):
        raise KernelTypeError(
            "Match branch count mismatch. "
            + f"Expected {len(constructor_names)}, found {len(expr.cases)}."
        )

    motive_type = whnf(infer_type(expr.motive, context, metavars, env), metavars, env)
    if not isinstance(motive_type, EPi):
        raise KernelTypeError("Match motive must be a function (Pi type).")
    motive_domain = whnf(motive_type.domain, metavars, env)
    if not is_def_eq(motive_domain, discriminee_type, context, metavars, env):
        raise KernelTypeError("Match motive domain mismatch with discriminee type.")

    for branch_expr, constructor_name in zip(
        expr.cases,
        constructor_names,
        strict=False,
    ):
        constructor_decl = env.get(constructor_name)
        if not isinstance(constructor_decl, ConstructorDeclaration):
            raise KernelTypeError(
                f"'{constructor_name}' is not a constructor declaration."
            )
        constructor_const = EConst(
            constructor_name,
            tuple(UnivLevelParam(p) for p in constructor_decl.level_params),
        )
        constructor_type = whnf(
            infer_type(constructor_const, context, metavars, env),
            metavars,
            env,
        )
        binders: list[tuple[str, Expr]] = []
        constructor_args: list[Expr] = []
        current_constructor_type = constructor_type
        while isinstance(current_constructor_type, EPi):
            binders.append(
                (current_constructor_type.var, current_constructor_type.domain)
            )
            constructor_args.append(EVar(current_constructor_type.var))
            current_constructor_type = current_constructor_type.body

        constructor_instance = build_app_chain(constructor_const, *constructor_args)
        expected_branch_type: Expr = EApp(expr.motive, constructor_instance)
        for var_name, domain in reversed(binders):
            expected_branch_type = EPi(var_name, domain, expected_branch_type)

        branch_type = infer_type(branch_expr, context, metavars, env)
        if not is_def_eq(branch_type, expected_branch_type, context, metavars, env):
            raise KernelTypeError(
                "Match branch type mismatch for constructor "
                + f"'{constructor_name}'."
            )

    return EApp(expr.motive, expr.discriminee)


def infer_type(
    expr: Expr,
    context: dict[str, Expr],
    metavars: dict[str, MetaVar],
    env: Environment | None = None,
) -> Expr:
    """Infer the type of an expression."""
    expr = instantiate_metavar(expr, metavars)

    match expr:
        case EMetaVar():
            return _infer_metavar(expr, metavars)
        case ESort():
            return _infer_sort(expr)
        case EVar():
            return _infer_var(expr, context)
        case EConst():
            return _infer_const(expr, context, env)
        case EPi():
            return _infer_pi(expr, context, metavars, env)
        case ELam():
            return _infer_lam(expr, context, metavars, env)
        case EApp():
            return _infer_app(expr, context, metavars, env)
        case EMatch():
            return _infer_match(expr, context, metavars, env)


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
