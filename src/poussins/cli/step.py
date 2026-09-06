"""Step-by-step proof execution subcommand for poussins CLI."""
from ..utils.logging import get_logger


def run_step(filepath: str, theorem: str | None = None):
    """Run step-by-step proof execution for a given file and theorem."""
    logger = get_logger(__name__)
    logger.info(f"Step-by-step execution (stub): {filepath}, theorem={theorem}")
