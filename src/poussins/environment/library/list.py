"""List declarations."""
from __future__ import annotations

from enum import Enum

from ...ast import EApp, EConst, EPi, ESort, EVar, UnivLevelParam
from ..declaration import ConstructorDeclaration, Declaration, InductiveDeclaration


class ListDeclaration(Enum):
    """Inductive declaration for lists."""

    LIST_DECLARATION = InductiveDeclaration(
        name="List",
        level_params=("u",),
        type=EPi("A", ESort(UnivLevelParam("u")), ESort(UnivLevelParam("u"))),
        constructor_names=("List.nil", "List.cons"),
    )

    LIST_NIL_DECLARATION = ConstructorDeclaration(
        name="List.nil",
        level_params=("u",),
        inductive_name="List",
        type=EPi(
            "A",
            ESort(UnivLevelParam("u")),
            EApp(EConst("List", (UnivLevelParam("u"),)), EVar("A")),
        ),
    )

    LIST_CONS_DECLARATION = ConstructorDeclaration(
        name="List.cons",
        level_params=("u",),
        inductive_name="List",
        type=EPi(
            "A",
            ESort(UnivLevelParam("u")),
            EPi(
                "head",
                EVar("A"),
                EPi(
                    "tail",
                    EApp(EConst("List", (UnivLevelParam("u"),)), EVar("A")),
                    EApp(EConst("List", (UnivLevelParam("u"),)), EVar("A")),
                ),
            ),
        ),
    )

    @property
    def declaration(self) -> Declaration:
        """Return the underlying declaration."""
        return self.value
