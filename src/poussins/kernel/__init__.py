"""
Kernel-level components of the proof system, including the core data structures and proof engine.
"""
from .goal import Goal
from .proof_engine import ProofEngine
from .proof_manager import ProofManager
from .proof_session import ProofSession
from .proof_state import ProofState
from .typecheck import infer_type, whnf, instantiate

__all__ = [
    "Goal",
    "ProofEngine",
    "ProofManager",
    "ProofSession",
    "ProofState",
    "infer_type",
    "whnf",
    "instantiate",
]
