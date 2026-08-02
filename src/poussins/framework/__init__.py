"""
Public DSL layer: Prop, Axiom, Theorem, Example, and aliases.
"""
from .axiom import Axiom
from .bool import Bool
from .inductive_type import InductiveType
from .proof_script import ProofScript
from .prop import Prop
from .nat import Nat
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
    "Bool",
    "InductiveType",
    "ProofScript",
    "Prop",
    "Nat",
    "Theorem",
    "Lemma",
    "Proposition",
    "Corollary",
    "Fact",
    "Remark",
    "Property",
    "Example",
]
