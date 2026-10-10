"""Public DSL layer: Prop, Axiom, Theorem, Example, and aliases."""
from .axiom import Axiom
from .bool import Bool
from .declared_type import DeclaredType
from .empty import Empty
from .environment import create_environment, create_standard_environment
from .fin import Fin
from .list import List
from .nat import Nat
from .option import Option
from .prod import Prod
from .proof_script import ProofScript
from .prop import Prop
from .quot import Quot
from .sigma import Sigma
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
    "DeclaredType",
    "Empty",
    "Example",
    "Fact",
    "Fin",
    "Lemma",
    "List",
    "Nat",
    "Option",
    "ProofScript",
    "Prop",
    "Prod",
    "Property",
    "Proposition",
    "Quot",
    "Remark",
    "Sigma",
    "Sum",
    "Theorem",
    "Unit",
    "Vector",
    "create_environment",
    "create_standard_environment",
]
