"""Public DSL layer: Prop, Axiom, Theorem, Example, and aliases."""
from .axiom import Axiom
from .bool import Bool
from .declaration import (
    declare_axiom,
    declare_definition,
    declare_inductive,
    declare_quot,
    declare_theorem,
)
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
    "Remark",
    "Sigma",
    "Sum",
    "Theorem",
    "Unit",
    "Vector",
    "create_environment",
    "create_standard_environment",
    "declare_axiom",
    "declare_definition",
    "declare_inductive",
    "declare_theorem",
    "declare_quot",
]
