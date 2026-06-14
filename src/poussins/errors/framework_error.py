"""
Framework-level errors.
"""
from .proof_error import ProofError


class FrameworkError(ProofError):
    """Raised when a framework construct is used incorrectly."""

    pass
