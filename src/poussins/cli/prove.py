"""
Batch proof execution subcommand for poussins CLI.
"""
import importlib.util
import sys
import os

from ..utils.logging import getLogger


def run_prove(filepath: str):
    """
    Run batch proof execution: import the file, collect all theorems/lemmas, and log their status.
    """
    logger = getLogger(__name__)

    file_abspath = os.path.abspath(filepath)
    file_dir = os.path.dirname(file_abspath)
    sys.path.insert(0, file_dir)
    sys.path.insert(0, os.getcwd())
    module_name = os.path.splitext(os.path.basename(filepath))[0]
    spec = importlib.util.spec_from_file_location(module_name, file_abspath)
    module = importlib.util.module_from_spec(spec)
    try:
        spec.loader.exec_module(module)
    except Exception as e:
        logger.error(f"Error executing {filepath}: {type(e).__name__}: {e}")
        return
