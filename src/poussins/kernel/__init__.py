"""Kernel-level components of the proof system."""
from .declare import (
    register_axiom,
    register_definition,
    register_inductive,
    register_quotient,
    register_theorem,
    validate_axiom,
    validate_definition,
    validate_inductive,
    validate_quotient,
    validate_theorem,
)
from .equality import is_alpha_eq, is_def_eq
from .eval import instantiate, normalize, whnf
from .goal import Goal
from .proof_engine import ProofEngine
from .proof_manager import ProofManager
from .proof_session import ProofSession
from .proof_state import ProofState
from .typecheck import infer_metavar_types, infer_type
from .unification import unify
from .univ import normalize_univ_level

__all__ = [
    "Goal",
    "ProofEngine",
    "ProofManager",
    "ProofSession",
    "ProofState",
    "normalize_univ_level",
    "infer_metavar_types",
    "infer_type",
    "instantiate",
    "is_alpha_eq",
    "is_def_eq",
    "normalize",
    "unify",
    "whnf",
    "register_axiom",
    "validate_axiom",
    "register_definition",
    "validate_definition",
    "register_theorem",
    "validate_theorem",
    "register_inductive",
    "validate_inductive",
    "register_quotient",
    "validate_quotient",
]
