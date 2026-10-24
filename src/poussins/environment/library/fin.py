"""Finite-index declarations."""
from __future__ import annotations

from enum import Enum

from ...ast import EApp, EConst, EPi, ESort, EVar, Sort, UnivLevelParam
from ..declaration import (
    ConstructorDeclaration,
    Declaration,
    InductiveDeclaration,
    RecursorDeclaration,
)


class FinDeclaration(Enum):
    """Inductive declaration for finite indices."""

    FIN_DECLARATION = InductiveDeclaration(
        name="Fin",
        level_params=(),
        type=EPi("n", EConst("Nat", ()), Sort.TYPE.sort),
        constructor_names=("Fin.zero", "Fin.succ"),
        recursor_names=("Fin.rec",)
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

    FIN_REC_DECLARATION = RecursorDeclaration(
        name="Fin.rec",
        level_params=("u",),
        inductive_name="Fin",
        num_params=0,
        num_indices=1,
        num_minors=2,
        type=EPi(
            "motive",
            EPi("n", EConst("Nat", ()),
                EPi(
                    "_",
                    EApp(EConst("Fin", ()), EVar("n")),
                    ESort(UnivLevelParam("u"))
                ),
            ),
            EPi(
                "zero",
                EPi(
                    "n",
                    EConst("Nat", ()),
                    EApp(
                        EApp(EVar("motive"), EApp(EConst("Nat.succ", ()), EVar("n"))),
                        EApp(EConst("Fin.zero", ()), EVar("n"))
                    ),
                ),
                EPi(
                    "succ",
                    EPi("n", EConst("Nat", ()),
                        EPi("value", EApp(EConst("Fin", ()), EVar("n")),
                            EPi(
                                "ih",
                                EApp(
                                    EApp(EVar("motive"), EVar("n")),
                                    EVar("value")
                                ),
                                EApp(
                                    EApp(
                                        EVar("motive"),
                                        EApp(EConst("Nat.succ", ()), EVar("n"))
                                    ),
                                    EApp(
                                        EApp(EConst("Fin.succ", ()), EVar("n")),
                                        EVar("value"),
                                    ),
                                ),
                            ),
                        ),
                    ),
                    EPi("n", EConst("Nat", ()),
                        EPi("f", EApp(EConst("Fin", ()), EVar("n")),
                            EApp(EApp(EVar("motive"), EVar("n")), EVar("f")),
                        ),
                    ),
                ),
            ),
        ),
    )

    @property
    def declaration(self) -> Declaration:
        """Return the underlying declaration."""
        return self.value
