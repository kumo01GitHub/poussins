"""Abstract Syntax Tree (AST) module."""
from .expr import EApp, EConst, ELam, EMatch, EMetaVar, EPi, ESort, EVar, Expr
from .ops import (
    app,
    collect_free_vars,
    collect_metavar_ids,
    collect_univ_level_params,
    collect_univ_levels,
    count_pi_binders,
    decompose_app,
    has_metavar,
    lam,
    pi,
    sort,
    substitute_expr,
    substitute_metavar,
    substitute_var,
    univ_level,
    univ_levels,
)
from .sorts import Sort
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
    "univ_level",
    "univ_levels",
    "sort",
    "app",
    "lam",
    "pi",
    "decompose_app",
    "substitute_var",
    "collect_univ_levels",
    "collect_univ_level_params",
    "collect_free_vars",
    "has_metavar",
    "substitute_metavar",
    "collect_metavar_ids",
    "substitute_expr",
    "count_pi_binders",
]
