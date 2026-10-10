"""Kernel-level components of the proof system."""
from .declare import (
    declare_axiom,
    declare_definition,
    declare_inductive,
    declare_quotient,
    declare_theorem,
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

__all__ = [
    "Goal",
    "ProofEngine",
    "ProofManager",
    "ProofSession",
    "ProofState",
    "infer_metavar_types",
    "infer_type",
    "instantiate",
    "is_alpha_eq",
    "is_def_eq",
    "normalize",
    "unify",
    "whnf",
    "declare_axiom",
    "declare_definition",
    "declare_theorem",
    "declare_inductive",
    "declare_quotient",
]
