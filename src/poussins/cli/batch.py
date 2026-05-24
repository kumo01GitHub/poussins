
"""Batch proof execution subcommand for poussins CLI."""


def run_batch(filepath: str):
    """
    Run batch proof execution: import the file, collect all theorems/lemmas, and log their status.
    """
    import importlib.util
    import sys
    import os

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
        print(f"[poussins] Error executing {filepath}: {e}")
        return
