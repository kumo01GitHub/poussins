"""Public DSL layer: Prop, Axiom, Theorem, Example, and aliases."""
from .axiom import Axiom
from .bool import Bool
from .empty import Empty
from .fin import Fin
from .inductive_type import InductiveType
from .list import List
from .nat import Nat
from .option import Option
from .prod import Prod
from .proof_script import ProofScript
from .prop import Prop
from .sum import Sum
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
from .unit import Unit
from .vector import Vector

__all__ = [
    "Axiom",
    "Bool",
    "Corollary",
    "Empty",
    "Example",
    "Fact",
    "Fin",
    "InductiveType",
    "Lemma",
    "List",
    "Nat",
    "Option",
    "ProofScript",
    "Prop",
    "Prod",
    "Property",
    "Proposition",
    "Remark",
    "Sum",
    "Theorem",
    "Unit",
    "Vector",
]
