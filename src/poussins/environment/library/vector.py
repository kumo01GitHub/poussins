"""Length-indexed vector declarations."""
from __future__ import annotations

from enum import Enum

from ...ast import EApp, EConst, EPi, ESort, EVar, UnivLevelParam
from ..declaration import ConstructorDeclaration, Declaration, InductiveDeclaration


class VectorDeclaration(Enum):
    """Inductive declaration for vectors."""

    VECTOR_DECLARATION = InductiveDeclaration(
        name="Vector",
        level_params=("u",),
        type=EPi(
            "A",
            ESort(UnivLevelParam("u")),
            EPi("n", EConst("Nat", ()), ESort(UnivLevelParam("u"))),
        ),
        constructor_names=("Vector.nil", "Vector.cons"),
    )

    VECTOR_NIL_DECLARATION = ConstructorDeclaration(
        name="Vector.nil",
        level_params=("u",),
        inductive_name="Vector",
        type=EPi(
            "A",
            ESort(UnivLevelParam("u")),
            EApp(
                EApp(EConst("Vector", (UnivLevelParam("u"),)), EVar("A")),
                EConst("Nat.zero", ()),
            ),
        ),
    )

    VECTOR_CONS_DECLARATION = ConstructorDeclaration(
        name="Vector.cons",
        level_params=("u",),
        inductive_name="Vector",
        type=EPi(
            "A",
            ESort(UnivLevelParam("u")),
            EPi(
                "n",
                EConst("Nat", ()),
                EPi(
                    "head",
                    EVar("A"),
                    EPi(
                        "tail",
                        EApp(
                            EApp(EConst("Vector", (UnivLevelParam("u"),)), EVar("A")),
                            EVar("n"),
                        ),
                        EApp(
                            EApp(EConst("Vector", (UnivLevelParam("u"),)), EVar("A")),
                            EApp(EConst("Nat.succ", ()), EVar("n")),
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
