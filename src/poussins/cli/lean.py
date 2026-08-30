"""Lean conversion subcommand.
"""
from ..utils.logging import getLogger


def run_lean2py(filepath: str, output: str | None = None):
    """Convert Lean file to Python DSL.
    """
    logger = getLogger(__name__)
    logger.info(f"Lean to Python conversion (stub): {filepath} -> {output}")


def run_py2lean(filepath: str, output: str | None = None):
    """Convert Python DSL file to Lean format.
    """
    logger = getLogger(__name__)
    logger.info(f"Python to Lean conversion (stub): {filepath} -> {output}")
