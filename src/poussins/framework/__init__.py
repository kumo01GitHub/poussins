"""
Public DSL layer: Prop, Axiom, Theorem, Example, and aliases.
"""
from .axiom import Axiom
from .environment import Declaration, DeclarationKind, Environment
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
    "Declaration",
    "DeclarationKind",
    "Environment",
]
