from __future__ import annotations
from enum import Enum

from .sort import Sort
from ..declaration import ConstructorDeclaration, Declaration, InductiveDeclaration
from ...ast.expr import EConst, EPi


class NatDeclaration(Enum):
    """
    Inductive declaration for natural numbers.
    """

    """
    Nat inductive declaration for natural numbers.
    """
    NAT_DECLARATION = InductiveDeclaration(
        name="Nat",
        level_params=(),
        type=Sort.TYPE.sort,
        constructor_names=("Nat.zero", "Nat.succ"),
    )
    """Nat.zero constructor declaration for natural numbers."""
    NAT_ZERO_DECLARATION = ConstructorDeclaration(
        name="Nat.zero",
        level_params=(),
        inductive_name="Nat",
        type=EConst("Nat", ()),
    )
    """Nat.succ constructor declaration for natural numbers."""
    NAT_SUCC_DECLARATION = ConstructorDeclaration(
        name="Nat.succ",
        level_params=(),
        inductive_name="Nat",
        type=EPi("n", EConst("Nat", ()), EConst("Nat", ())),
    )


    @property
    def declaration(self) -> Declaration:
        """Return the underlying declaration."""
        return self.value
