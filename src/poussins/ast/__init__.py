"""Abstract Syntax Tree (AST) module."""
from .expr import EApp, EConst, ELam, EMatch, EMetaVar, EPi, ESort, EVar, Expr
from .ops import (
    app,
    collect_free_vars,
    collect_metavar_ids,
    collect_univ_levels,
    count_pi_binders,
    flatten_app_chain,
    has_metavar,
    lam,
    pi,
    substitute_expr,
    substitute_expr_var,
    substitute_metavar,
)
from .sort import Sort
from .universe import (
    UnivLevel,
    UnivLevelIMax,
    UnivLevelMax,
    UnivLevelParam,
    UnivLevelSucc,
    UnivLevelZero,
)

__all__ = [
    # Expr classes
    "Expr",
    "EVar",
    "EConst",
    "EPi",
    "ELam",
    "EApp",
    "EMetaVar",
    "ESort",
    "EMatch",
    # Universe level classes
    "UnivLevel",
    "UnivLevelZero",
    "UnivLevelSucc",
    "UnivLevelParam",
    "UnivLevelMax",
    "UnivLevelIMax",
    # Sort classes
    "Sort",
    # Expr operations
    "app",
    "lam",
    "pi",
    "has_metavar",
    "flatten_app_chain",
    "substitute_metavar",
    "collect_metavar_ids",
    "substitute_expr_var",
    "collect_free_vars",
    "substitute_expr",
    "collect_univ_levels",
    "count_pi_binders",
]
