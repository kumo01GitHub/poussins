"""Integration module for Spark."""
from __future__ import annotations

from .registry import ProofTaskRegistry
from .runner import ProofRunner

__all__ = [
    "ProofRunner",
    "ProofTaskRegistry",
]
