"""
Derived tactics.
"""
from ..kernel import ProofEngine
from ..tactics import intro


def intros(proof_engine: ProofEngine, hyp_names: list[str]):
    for hyp_name in hyp_names:
        intro(proof_engine, hyp_name)
