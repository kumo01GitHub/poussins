"""Formula kernel: AST nodes and proof terms for propositional logic."""

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
from .proof_terms import (
    ProofTerm,
    PMetaVar,
    PVar,
    PLam,
    PApp,
    PAndI,
    PAndE1,
    PAndE2,
    POrIL,
    POrIR,
    POrE,
    PTrueI,
    PFalseE,
    PExI,
    PExE,
)

__all__ = [
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
    "PAndE1",
    "PAndE2",
    "POrIL",
    "POrIR",
    "POrE",
    "PTrueI",
    "PFalseE",
    "PExI",
    "PExE",
]
