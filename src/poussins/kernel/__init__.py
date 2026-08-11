"""
Kernel-level components of the proof system, including the core data structures and proof engine.
"""
from .goal import Goal
from .proof_engine import ProofEngine
from .proof_manager import ProofManager
from .proof_session import ProofSession
from .proof_state import ProofState
from .typecheck import infer_type, whnf, instantiate, is_alpha_eq, is_def_eq, unify, infer_metavar_types

__all__ = [
    "Goal",
    "ProofEngine",
    "ProofManager",
    "ProofSession",
    "ProofState",
    "infer_type",
    "whnf",
    "instantiate",
    "is_alpha_eq",
    "is_def_eq",
    "unify",
    "infer_metavar_types",
]
