from __future__ import annotations

from enum import Enum

from ...ast.expr import EApp, EConst, ELam, EPi, ESort, EVar, UnivLevelParam
from ..declaration import (
    ConstructorDeclaration,
    Declaration,
    DefinitionDeclaration,
    InductiveDeclaration,
    RecursorDeclaration,
)
from .sort import Sort


class NatDeclaration(Enum):
    """Inductive declaration for natural numbers."""

    """Nat inductive declaration for natural numbers."""
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

    """Nat.rec recursor declaration for natural numbers (Mathematical Induction / Primitive Recursion)."""
    NAT_REC_DECLARATION = RecursorDeclaration(
        name="Nat.rec",
        level_params=("u",),
        inductive_name="Nat",
        num_params=0,
        num_indices=0,
        num_minors=2,
        type=EPi("motive", EPi("_", EConst("Nat", ()), ESort(UnivLevelParam("u"))),
            EPi("zero_case", EApp(EVar("motive"), EConst("Nat.zero", ())),
                EPi("succ_case", EPi("n", EConst("Nat", ()), EPi("ih", EApp(EVar("motive"), EVar("n")), EApp(EVar("motive"), EApp(EConst("Nat.succ", ()), EVar("n"))))),
                    EPi("k", EConst("Nat", ()),
                        EApp(EVar("motive"), EVar("k"))
                    )
                )
            )
        )
    )

    """Nat.add definition declaration for natural numbers."""
    NAT_ADD_DECLARATION = DefinitionDeclaration(
        name="Nat.add",
        level_params=(),
        type=EPi("n", EConst("Nat", ()), EPi("m", EConst("Nat", ()), EConst("Nat", ()))),
        value=ELam("n", EConst("Nat", ()), ELam("m", EConst("Nat", ()), EVar("m"))),
    )

    @property
    def declaration(self) -> Declaration:
        """Return the underlying declaration."""
        return self.value
