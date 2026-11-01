"""Kernel-level evaluation functions for expressions."""
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
    app,
    decompose_app,
    instantiate_binder,
    substitute_metavar,
)
from ..environment import (
    ConstructorDeclaration,
    DefinitionDeclaration,
    Environment,
    InductiveDeclaration,
    RecursorDeclaration,
)
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
    def occurs_in(target_name: str, expr: Expr) -> bool:
        """Recursively check if `target_name` (as EConst) occurs in `expr`."""
        match expr:
            case EConst(name=name) if name == target_name:
                return True
            case EPi(_, domain, body) | ELam(_, domain, body):
                return occurs_in(target_name, domain) or occurs_in(target_name, body)
            case EApp(fn, arg):
                return occurs_in(target_name, fn) or occurs_in(target_name, arg)
            case ESort(_) | EFVar(_) | EBVar(_) | EMetaVar(_) | EConst(_):
                return False
            case _:
                return False

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

        case EApp(fn, arg) as app_expr:
            head, args = decompose_app(app_expr)

            # 1. Check if head is a Recursor and arguments are sufficient to reduce
            if isinstance(head, EConst) and env is not None:
                decl = env.get(head.name)
                if isinstance(decl, RecursorDeclaration):
                    total_fixed = (
                        decl.num_params + 1
                        + decl.num_minors
                        + decl.num_indices + 1
                    )
                    if len(args) >= total_fixed:
                        discriminee_idx = (
                            decl.num_params + 1
                            + decl.num_minors
                            + decl.num_indices
                        )
                        discriminee = args[discriminee_idx]
                        discriminee_whnf = whnf(discriminee, metavars, env, unfolding)

                        d_head, d_args = decompose_app(discriminee_whnf)
                        ind_decl = env.get(decl.inductive_name)
                        if (
                            isinstance(d_head, EConst)
                            and isinstance(ind_decl, InductiveDeclaration)
                        ):
                            ctor_names = ind_decl.constructor_names
                            if d_head.name in ctor_names:
                                ctor_idx = ctor_names.index(d_head.name)
                                minor_start = decl.num_params + 1
                                minor_expr = args[minor_start + ctor_idx]

                                current_val = minor_expr

                                # Dynamically inspect constructor signature
                                # to handle parameters and recursive fields generically
                                ctor_decl = env.get(d_head.name)
                                if isinstance(ctor_decl, ConstructorDeclaration):
                                    ctor_type_curr = ctor_decl.type
                                    # Skip parameters
                                    for _ in range(decl.num_params):
                                        if isinstance(ctor_type_curr, EPi):
                                            ctor_type_curr = ctor_type_curr.body

                                    # Inspect constructor argument binders
                                    arg_idx = 0
                                    while (
                                        isinstance(ctor_type_curr, EPi)
                                        and arg_idx < len(d_args)
                                    ):
                                        param_domain = ctor_type_curr.domain
                                        is_recursive = occurs_in(
                                            decl.inductive_name,
                                            param_domain
                                        )

                                        ctor_arg = d_args[arg_idx]
                                        current_val = EApp(current_val, ctor_arg)

                                        if is_recursive:
                                            # Compute inductive hypothesis (IH)
                                            rec_args = list(args)
                                            rec_args[discriminee_idx] = ctor_arg
                                            ih = whnf(
                                                app(head, *rec_args),
                                                metavars,
                                                env,
                                                unfolding,
                                            )
                                            current_val = EApp(current_val, ih)

                                        ctor_type_curr = ctor_type_curr.body
                                        arg_idx += 1

                                # Apply any remaining extra arguments
                                extra_args = args[discriminee_idx + 1:]
                                for extra in extra_args:
                                    current_val = EApp(current_val, extra)

                                return whnf(current_val, metavars, env, unfolding)

            # 2. Standard Application beta-reduction
            fn_whnf = whnf(fn, metavars, env, unfolding)
            if isinstance(fn_whnf, ELam):
                new_expr = instantiate_binder(fn_whnf.body, arg)
                return whnf(new_expr, metavars, env, unfolding)
            return EApp(fn_whnf, arg)

        case (ESort(_) | EFVar(_) | EBVar(_) | ELam(_, _, _) | EPi(_, _, _) | EMetaVar(_)):
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
        case ESort() | EFVar() | EBVar() | EConst() | EMetaVar():
            return e
