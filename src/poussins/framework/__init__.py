"""
Public DSL layer: Prop, Axiom, Theorem, Example, and aliases.
"""
from .axiom import Axiom
from .proof_script import ProofScript
from .prop import Prop
from .theorem import (
    Theorem,
    Lemma,
    Proposition,
    Corollary,
    Fact,
    Remark,
    Property,
    Example,
)


__all__ = [
    "Axiom",
    "ProofScript",
    "Prop",
    "Theorem",
    "Lemma",
    "Proposition",
    "Corollary",
    "Fact",
    "Remark",
    "Property",
    "Example",
]
