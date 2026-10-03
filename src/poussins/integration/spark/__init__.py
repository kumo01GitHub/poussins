"""Integration module for Spark."""
from .registry import ProofTaskRegistry
from .runner import ProofRunner

__all__ = [
    "ProofRunner",
    "ProofTaskRegistry",
]
