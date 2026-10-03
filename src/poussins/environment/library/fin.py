"""Finite-index declarations."""
from __future__ import annotations

from enum import Enum

from ...ast import EApp, EConst, EPi, EVar
from ..declaration import ConstructorDeclaration, Declaration, InductiveDeclaration
from .sort import Sort


class FinDeclaration(Enum):
    """Inductive declaration for finite indices."""

    FIN_DECLARATION = InductiveDeclaration(
        name="Fin",
        level_params=(),
        type=EPi("n", EConst("Nat", ()), Sort.TYPE.sort),
        constructor_names=("Fin.zero", "Fin.succ"),
    )

    FIN_ZERO_DECLARATION = ConstructorDeclaration(
        name="Fin.zero",
        level_params=(),
        inductive_name="Fin",
        type=EPi(
            "n",
            EConst("Nat", ()),
            EApp(EConst("Fin", ()), EApp(EConst("Nat.succ", ()), EVar("n"))),
        ),
    )

    FIN_SUCC_DECLARATION = ConstructorDeclaration(
        name="Fin.succ",
        level_params=(),
        inductive_name="Fin",
        type=EPi(
            "n",
            EConst("Nat", ()),
            EPi(
                "value",
                EApp(EConst("Fin", ()), EVar("n")),
                EApp(EConst("Fin", ()), EApp(EConst("Nat.succ", ()), EVar("n"))),
            ),
        ),
    )

    @property
    def declaration(self) -> Declaration:
        """Return the underlying declaration."""
        return self.value
