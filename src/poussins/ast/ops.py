"""AST operation utilities for expression traversal, substitution, and analysis."""
from __future__ import annotations

from .expr import (
    EApp,
    EConst,
    ELam,
    EMatch,
    EMetaVar,
    EPi,
    ESort,
    EVar,
    Expr,
)


def has_metavar(expr: Expr) -> bool:
    """Check if the expression contains any meta-variables (holes)."""
    match expr:
        case EMetaVar(_):
            return True
        case ESort(_) | EVar(_) | EConst(_):
            return False
        case EPi(_, domain, body) | ELam(_, domain, body):
            return has_metavar(domain) or has_metavar(body)
        case EApp(fn, arg):
            return has_metavar(fn) or has_metavar(arg)
        case EMatch(_, discriminee, motive, cases):
            return (
                has_metavar(discriminee)
                or has_metavar(motive)
                or any(has_metavar(c) for c in cases)
            )
        case _:
            raise NotImplementedError(f"Unknown expression node: {expr}")


def substitute_metavar(
    expr: Expr, target_goal_id: str, replacement: Expr | None
) -> Expr:
    """Substitute all occurrences of the meta-variable."""
    if replacement is None:
        raise ValueError("Replacement expression cannot be None.")

    match expr:
        case EMetaVar(goal_id):
            return replacement if goal_id == target_goal_id else expr
        case ESort(_) | EVar(_) | EConst(_):
            return expr
        case EPi(var, domain, body):
            return EPi(
                var,
                substitute_metavar(domain, target_goal_id, replacement),
                substitute_metavar(body, target_goal_id, replacement)
            )
        case ELam(var, domain, body):
            return ELam(
                var,
                substitute_metavar(domain, target_goal_id, replacement),
                substitute_metavar(body, target_goal_id, replacement)
            )
        case EApp(fn, arg):
            return EApp(
                substitute_metavar(fn, target_goal_id, replacement),
                substitute_metavar(arg, target_goal_id, replacement)
            )
        case EMatch(inductive_name, discriminee, motive, cases):
            return EMatch(
                inductive_name,
                substitute_metavar(discriminee, target_goal_id, replacement),
                substitute_metavar(motive, target_goal_id, replacement),
                tuple(substitute_metavar(c, target_goal_id, replacement) for c in cases)
            )
        case _:
            raise NotImplementedError(f"Unknown expression node: {expr}")


def substitute_expr_var(expr: Expr, var_name: str, replacement: Expr) -> Expr:
    """Substitute all occurrences of the variable."""
    replacement_fvs = collect_free_vars(replacement)

    def subst(e: Expr) -> Expr:
        match e:
            case EVar(name):
                return replacement if name == var_name else e
            case ESort(_) | EConst(_) | EMetaVar(_):
                return e

            case EPi(var, domain, body):
                new_domain = subst(domain)
                if var == var_name:
                    return EPi(var, new_domain, body)

                if var in replacement_fvs:
                    new_var = var + "_"
                    while new_var in replacement_fvs or new_var == var_name:
                        new_var += "_"
                    alpha_body = substitute_expr_var(body, var, EVar(new_var))
                    return EPi(
                        new_var,
                        new_domain,
                        substitute_expr_var(alpha_body, var_name, replacement)
                    )

                return EPi(var, new_domain, subst(body))

            case ELam(var, domain, body):
                new_domain = subst(domain)
                if var == var_name:
                    return ELam(var, new_domain, body)

                if var in replacement_fvs:
                    new_var = var + "_"
                    while new_var in replacement_fvs or new_var == var_name:
                        new_var += "_"
                    alpha_body = substitute_expr_var(body, var, EVar(new_var))
                    return ELam(
                        new_var,
                        new_domain,
                        substitute_expr_var(alpha_body, var_name, replacement)
                    )

                return ELam(var, new_domain, subst(body))

            case EApp(fn, arg):
                return EApp(subst(fn), subst(arg))
            case EMatch(inductive_name, discriminee, motive, cases):
                return EMatch(
                    inductive_name,
                    subst(discriminee),
                    subst(motive),
                    tuple(subst(c) for c in cases)
                )
            case _:
                raise NotImplementedError(f"Unknown expression node: {e}")

    return subst(expr)


def collect_metavar_ids(expr: Expr) -> list[str]:
    """Collect all unique meta-variable goal IDs present in the expression."""
    ordered_ids: list[str] = []

    def _collect(e: Expr) -> None:
        match e:
            case EMetaVar(goal_id):
                if goal_id not in ordered_ids:
                    ordered_ids.append(goal_id)
            case ESort(_) | EVar(_) | EConst(_):
                pass
            case EPi(_, domain, body) | ELam(_, domain, body):
                _collect(domain)
                _collect(body)
            case EApp(fn, arg):
                _collect(fn)
                _collect(arg)
            case EMatch(_, discriminee, motive, cases):
                _collect(discriminee)
                _collect(motive)
                for case_expr in cases:
                    _collect(case_expr)
            case _:
                raise NotImplementedError(f"Unknown expression node: {e}")

    _collect(expr)
    return ordered_ids


def collect_free_vars(expr: Expr) -> set[str]:
    """Collect all free variable names present in the expression."""
    match expr:
        case EVar(name):
            return {name}
        case ESort(_) | EConst(_) | EMetaVar(_):
            return set()
        case EPi(var, domain, body) | ELam(var, domain, body):
            return collect_free_vars(domain) | (collect_free_vars(body) - {var})
        case EApp(fn, arg):
            return collect_free_vars(fn) | collect_free_vars(arg)
        case EMatch(_, discriminee, motive, cases):
            fvs = collect_free_vars(discriminee) | collect_free_vars(motive)
            for c in cases:
                fvs |= collect_free_vars(c)
            return fvs
        case _:
            raise NotImplementedError(f"Unknown expression node: {expr}")
