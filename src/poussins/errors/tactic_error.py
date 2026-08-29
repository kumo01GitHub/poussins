"""
Tactic-level errors.
"""
from .proof_error import ProofError


class TacticError(ProofError):
    """
    Raised when a tactic fails to apply.
    """

    pass
