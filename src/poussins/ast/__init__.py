"""
Abstract Syntax Tree (AST) module.
"""
from .expr import Expr, ESort, EVar, EConst, EPi, ELam, EApp, EMatch, EMetaVar
from .ops import has_metavar, substitute_metavar, substitute_expr_var, collect_metavar_ids, collect_free_vars
from .universe import UnivLevel, UnivLevelZero, UnivLevelSucc, UnivLevelParam, UnivLevelMax, UnivLevelIMax


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
