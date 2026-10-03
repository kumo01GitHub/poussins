"""Sum-type declarations."""
from __future__ import annotations

from enum import Enum

from ...ast import EApp, EConst, EPi, ESort, EVar, UnivLevelParam
from ..declaration import ConstructorDeclaration, Declaration, InductiveDeclaration


class SumDeclaration(Enum):
    """Inductive declaration for binary sums."""

    SUM_DECLARATION = InductiveDeclaration(
        name="Sum",
        level_params=("u",),
        type=EPi(
            "A",
            ESort(UnivLevelParam("u")),
            EPi("B", ESort(UnivLevelParam("u")), ESort(UnivLevelParam("u"))),
        ),
        constructor_names=("Sum.inl", "Sum.inr"),
    )

    SUM_INL_DECLARATION = ConstructorDeclaration(
        name="Sum.inl",
        level_params=("u",),
        inductive_name="Sum",
        type=EPi(
            "A",
            ESort(UnivLevelParam("u")),
            EPi(
                "B",
                ESort(UnivLevelParam("u")),
                EPi(
                    "value",
                    EVar("A"),
                    EApp(
                        EApp(EConst("Sum", (UnivLevelParam("u"),)), EVar("A")),
                        EVar("B"),
                    ),
                ),
            ),
        ),
    )

    SUM_INR_DECLARATION = ConstructorDeclaration(
        name="Sum.inr",
        level_params=("u",),
        inductive_name="Sum",
        type=EPi(
            "A",
            ESort(UnivLevelParam("u")),
            EPi(
                "B",
                ESort(UnivLevelParam("u")),
                EPi(
                    "value",
                    EVar("B"),
                    EApp(
                        EApp(EConst("Sum", (UnivLevelParam("u"),)), EVar("A")),
                        EVar("B"),
                    ),
                ),
            ),
        ),
    )

    @property
    def declaration(self) -> Declaration:
        """Return the underlying declaration."""
        return self.value
