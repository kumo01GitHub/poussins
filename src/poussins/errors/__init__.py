"""
Error classes for Poussins.
"""
from .framework_error import FrameworkError
from .kernel_error import KernelTypeError, KernelStateError, KernelValueError
from .proof_error import ProofError
from .tactic_error import TacticError

__all__ = [
    "ProofError",
    "FrameworkError",
    "KernelTypeError",
    "KernelStateError",
    "KernelValueError",
    "TacticError",
]
