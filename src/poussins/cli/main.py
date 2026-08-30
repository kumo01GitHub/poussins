"""Command-line entrypoint wiring for poussins.
"""
import argparse

from .lean import run_lean2py, run_py2lean
from .prove import run_prove
from .step import run_step


def main():
    """Parse CLI arguments and dispatch to the selected subcommand.
    """
    parser = argparse.ArgumentParser(description="poussins command line")
    subparsers = parser.add_subparsers(dest="subcmd", required=True)


    # prove
    p_prove = subparsers.add_parser("prove", help="Batch proof execution (.py)")
    _ = p_prove.add_argument("filepath", help=".py file with theorems/lemmas")

    # step
    p_step = subparsers.add_parser("step", help="Step-by-step proof execution")
    _ = p_step.add_argument("filepath", help=".py file with theorems/lemmas")
    _ = p_step.add_argument("--theorem", help="Theorem name to step through", default=None)

    # lean2py
    p_lean2py = subparsers.add_parser("lean2py", help="Convert Lean file to Python DSL")
    _ = p_lean2py.add_argument("filepath", help=".lean file to convert")
    _ = p_lean2py.add_argument("--output", help="Output file path", default=None)

    # py2lean
    p_py2lean = subparsers.add_parser("py2lean", help="Convert Python DSL to Lean format")
    _ = p_py2lean.add_argument("filepath", help=".py file to convert")
    _ = p_py2lean.add_argument("--output", help="Output file path", default=None)

    args = parser.parse_args()

    if args.subcmd == "prove":
        run_prove(args.filepath)
    elif args.subcmd == "step":
        run_step(args.filepath, args.theorem)
    elif args.subcmd == "lean2py":
        run_lean2py(args.filepath, args.output)
    elif args.subcmd == "py2lean":
        run_py2lean(args.filepath, args.output)
