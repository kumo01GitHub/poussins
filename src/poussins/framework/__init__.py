"""Public DSL layer: Prop, Axiom, Theorem, Example, and aliases."""
from .axiom import Axiom
from .bool import Bool
from .inductive_type import InductiveType
from .nat import Nat
from .proof_script import ProofScript
from .prop import Prop
from .theorem import (
    Corollary,
    Example,
    Fact,
    Lemma,
    Property,
    Proposition,
    Remark,
    Theorem,
)

__all__ = [
    "Axiom",
    "Bool",
    "Corollary",
    "Example",
    "Fact",
    "InductiveType",
    "Lemma",
    "Nat",
    "ProofScript",
    "Prop",
    "Property",
    "Proposition",
    "Remark",
    "Theorem",
]
