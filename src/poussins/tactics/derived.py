"""
"""

from .primitive import intro
from ..kernel.proof_engine import ProofEngine


def intros(proof_engine: ProofEngine, hyp_names: list[str]):
    for hyp_name in hyp_names:
        intro(proof_engine, hyp_name)
