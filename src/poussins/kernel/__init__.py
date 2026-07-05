"""
Kernel-level components of the proof system, including the core data structures and proof engine.
"""
from .goal import Goal, Context, ProofAssurance
from .proof_engine import ProofEngine
from .proof_state import ProofState
from .typecheck import infer_expr, check_expr

__all__ = [
    "Goal",
    "Context",
    "ProofAssurance",
    "ProofEngine",
    "ProofState",
    "infer_expr",
    "check_expr",
]
