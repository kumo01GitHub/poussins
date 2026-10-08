"""Abstract Syntax Tree (AST) module."""
from .expr import EApp, EConst, ELam, EMatch, EMetaVar, EPi, ESort, EVar, Expr
from .ops import (
    build_app_chain,
    build_lambda_chain,
    collect_free_vars,
    collect_metavar_ids,
    flatten_app_chain,
    has_metavar,
    substitute_expr,
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
    # Universe level classes
    "UnivLevel",
    "UnivLevelZero",
    "UnivLevelSucc",
    "UnivLevelParam",
    "UnivLevelMax",
    "UnivLevelIMax",
    # Expr operations
    "has_metavar",
    "build_app_chain",
    "build_lambda_chain",
    "flatten_app_chain",
    "substitute_metavar",
    "collect_metavar_ids",
    "substitute_expr_var",
    "collect_free_vars",
    "substitute_expr",
]
