"""
"""
from .constants import LogicalSide
from .formulas import (
    Formula,
    FVar,
    FImpl,
    FAnd,
    FOr,
    FTrue,
    FFalse,
    FExists,
)
from .ops import collect_meta_var_ids, substitute_meta_var
from .proof_terms import (
    ProofTerm,
    PMetaVar,
    PVar,
    PLam,
    PApp,
    PAndI,
    PAndE,
    POrIL,
    POrIR,
    POrE,
    PTrueI,
    PFalseE,
    PExI,
    PExE,
)

__all__ = [
    # Constants
    "LogicalSide",
    # Formula AST
    "Formula",
    "FVar",
    "FImpl",
    "FAnd",
    "FOr",
    "FTrue",
    "FFalse",
    "FExists",
    # ProofTerm AST
    "ProofTerm",
    "PMetaVar",
    "PVar",
    "PLam",
    "PApp",
    "PAndI",
    "PAndE",
    "POrIL",
    "POrIR",
    "POrE",
    "PTrueI",
    "PFalseE",
    "PExI",
    "PExE",
    # Operations on AST
    "collect_meta_var_ids",
    "substitute_meta_var",
]
