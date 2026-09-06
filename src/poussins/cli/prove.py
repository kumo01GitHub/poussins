"""Batch proof execution subcommand for poussins CLI."""
import importlib.util
import os
import sys

from ..utils.logging import get_logger


def run_prove(filepath: str):
    """Run batch proof execution: import the file, collect all theorems/lemmas."""
    logger = get_logger(__name__)

    file_abspath = os.path.abspath(filepath)
    file_dir = os.path.dirname(file_abspath)
    sys.path.insert(0, file_dir)
    sys.path.insert(0, os.getcwd())
    module_name = os.path.splitext(os.path.basename(filepath))[0]
    spec = importlib.util.spec_from_file_location(module_name, file_abspath)

    if spec is None:
        logger.exception(f"Could not load spec for {filepath}.")
    else:
        module = importlib.util.module_from_spec(spec)
        loder = spec.loader
        if loder is None:
            logger.exception(f"Could not load module for {filepath}.")
        else:
            try:
                loder.exec_module(module)
            except Exception as e:
                logger.exception(f"Error executing {filepath}: {type(e).__name__}: {e}")
