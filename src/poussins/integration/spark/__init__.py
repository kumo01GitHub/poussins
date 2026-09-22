"""Integration module for Spark."""
from .context import SparkProofContext
from .registry import ProofTaskRegistry

__all__ = [
    "SparkProofContext",
    "ProofTaskRegistry",
]
