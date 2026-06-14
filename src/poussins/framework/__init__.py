"""
Public DSL layer: Prop, Axiom, Theorem, Example, and aliases.
"""
from .axiom import Axiom
from .declaration import Declaration
from .environment import Environment
from .proof_driver import ProofDriver
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
    "Declaration",
    "Environment",
    "ProofDriver",
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
