"""Kernel-level evaluation functions for expressions."""
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
    flatten_app_chain,
    substitute_expr_var,
    substitute_metavar,
)
from ..environment import DefinitionDeclaration, Environment, InductiveDeclaration
from .proof_state import MetaVar


def instantiate_metavar(expr: Expr, metavars: dict[str, MetaVar]) -> Expr:
    """Instantiate assigned metavariables in an expression."""
    current = expr
    for goal_id, metavar in metavars.items():
        if metavar.is_assigned:
            current = substitute_metavar(current, goal_id, metavar.assignment)
    return current


def instantiate(expr: Expr, metavars: dict[str, MetaVar]) -> Expr:
    """Recursively replace all assigned metavariables in an expression."""
    current = expr
    while True:
        next_term = instantiate_metavar(current, metavars)
        if next_term == current:
            break
        current = next_term
    return current


def whnf(
    expr: Expr,
    metavars: dict[str, MetaVar],
    env: Environment | None = None,
    unfolding: frozenset[str] | None = None,
) -> Expr:
    """Reduce an expression to weak head normal form."""
    if unfolding is None:
        unfolding = frozenset()

    expr = instantiate_metavar(expr, metavars)
    match expr:
        case EConst(name, _):
            if env is not None and name not in unfolding:
                decl = env.get(name)
                if isinstance(decl, DefinitionDeclaration):
                    return whnf(decl.value, metavars, env, unfolding | {name})
            return expr
        case EApp(fn, arg):
            fn_whnf = whnf(fn, metavars, env, unfolding)
            if isinstance(fn_whnf, ELam):
                new_expr = substitute_expr_var(fn_whnf.body, fn_whnf.var, arg)
                return whnf(new_expr, metavars, env, unfolding)
            return EApp(fn_whnf, arg)
        case EMatch(inductive_name, discriminee, motive, cases):
            discriminee_whnf = whnf(discriminee, metavars, env, unfolding)

            if env is not None:
                decl = env.get(inductive_name)
                if isinstance(decl, InductiveDeclaration):
                    discriminee_head, discriminee_args = flatten_app_chain(
                        discriminee_whnf
                    )
                    if isinstance(discriminee_head, EConst):
                        constructor_names = decl.constructor_names
                        if (
                            discriminee_head.name in constructor_names
                            and len(cases) == len(constructor_names)
                        ):
                            branch_index = constructor_names.index(
                                discriminee_head.name
                            )
                            branch_expr = cases[branch_index]
                            reduced_branch: Expr = branch_expr

                            for constructor_arg in discriminee_args:
                                reduced_head = whnf(
                                    reduced_branch,
                                    metavars,
                                    env,
                                    unfolding,
                                )
                                if isinstance(reduced_head, ELam):
                                    reduced_branch = substitute_expr_var(
                                        reduced_head.body,
                                        reduced_head.var,
                                        constructor_arg,
                                    )
                                else:
                                    reduced_branch = EApp(
                                        reduced_branch,
                                        constructor_arg,
                                    )

                            return whnf(reduced_branch, metavars, env, unfolding)

            return EMatch(inductive_name, discriminee_whnf, motive, cases)
        case (
            ESort(_)
            | EVar(_)
            | ELam(_, _, _)
            | EPi(_, _, _)
            | EMetaVar(_)
        ):
            return expr


def normalize(
    expr: Expr,
    metavars: dict[str, MetaVar] | None = None,
    env: Environment | None = None,
    unfolding: frozenset[str] | None = None,
) -> Expr:
    """Fully normalize an expression by evaluating it to Strong Normal Form."""
    actual_metavars = metavars if metavars is not None else {}

    e = whnf(expr, actual_metavars, env, unfolding)

    match e:
        case EApp(fn, arg):
            return EApp(
                normalize(fn, actual_metavars, env, unfolding),
                normalize(arg, actual_metavars, env, unfolding),
            )
        case ELam(var, domain, body):
            return ELam(
                var,
                normalize(domain, actual_metavars, env, unfolding),
                normalize(body, actual_metavars, env, unfolding),
            )
        case EPi(var, domain, body):
            return EPi(
                var,
                normalize(domain, actual_metavars, env, unfolding),
                normalize(body, actual_metavars, env, unfolding),
            )
        case EMatch(inductive_name, discriminee, motive, cases):
            return EMatch(
                inductive_name=inductive_name,
                discriminee=normalize(discriminee, actual_metavars, env, unfolding),
                motive=normalize(motive, actual_metavars, env, unfolding),
                cases=tuple(
                    normalize(case_expr, actual_metavars, env, unfolding)
                    for case_expr in cases
                ),
            )
        case ESort() | EVar() | EConst() | EMetaVar():
            return e
