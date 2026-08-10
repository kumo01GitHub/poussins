"""
Step-by-step proof execution subcommand for poussins CLI.
"""
from ..utils.logging import getLogger

def run_step(filepath: str, theorem: str | None = None):
    """
    Run step-by-step proof execution for a given file and theorem (stub).
    """
    logger = getLogger(__name__)
    logger.info(f"Step-by-step execution (stub): {filepath}, theorem={theorem}")
