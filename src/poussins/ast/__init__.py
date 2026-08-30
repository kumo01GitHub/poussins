"""Abstract Syntax Tree (AST) module.
"""
from .expr import EApp, EConst, ELam, EMatch, EMetaVar, EPi, ESort, EVar, Expr
from .ops import (
    collect_free_vars,
    collect_metavar_ids,
    has_metavar,
    substitute_expr_var,
    substitute_metavar,
)
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
    # Expr operations
    "has_metavar",
    "substitute_metavar",
    "collect_metavar_ids",
    "substitute_expr_var",
    "collect_free_vars",
    # Universe level classes
    "UnivLevel",
    "UnivLevelZero",
    "UnivLevelSucc",
    "UnivLevelParam",
    "UnivLevelMax",
    "UnivLevelIMax",
]
