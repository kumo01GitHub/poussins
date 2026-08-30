"""Kernel-level errors."""
from .proof_error import ProofError


class KernelTypeError(ProofError):
    """Raised when a proof term fails kernel type checking."""

    pass


class KernelStateError(ProofError):
    """Raised when a proof term fails kernel state checking."""

    pass


class KernelValueError(ProofError):
    """Raised when a proof term has an invalid value (e.g., unbound meta-variable)."""

    pass
