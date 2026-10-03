"""Integration-level errors."""
from .proof_error import ProofError


class IntegrationError(ProofError):
    """Raised when an integration construct is used incorrectly."""

    pass


class SparkIntegrationError(IntegrationError):
    """Raised when a Spark integration construct is used incorrectly."""

    pass
