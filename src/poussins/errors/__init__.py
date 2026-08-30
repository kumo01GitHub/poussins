"""Error classes for Poussins."""
from .framework_error import FrameworkError
from .kernel_error import KernelStateError, KernelTypeError, KernelValueError
from .proof_error import ProofError
from .tactic_error import TacticError

__all__ = [
    "FrameworkError",
    "KernelStateError",
    "KernelTypeError",
    "KernelValueError",
    "ProofError",
    "TacticError",
]
