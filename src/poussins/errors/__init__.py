"""Error classes for Poussins."""
from .framework_error import FrameworkError
from .integration_error import IntegrationError, SparkIntegrationError
from .kernel_error import KernelStateError, KernelTypeError, KernelValueError
from .proof_error import ProofError
from .tactic_error import TacticError

__all__ = [
    "FrameworkError",
    "IntegrationError",
    "KernelStateError",
    "KernelTypeError",
    "KernelValueError",
    "ProofError",
    "SparkIntegrationError",
    "TacticError",
]
