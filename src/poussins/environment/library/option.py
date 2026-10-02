"""Optional-value declarations."""
from __future__ import annotations

from enum import Enum

from ...ast import EApp, EConst, EPi, ESort, EVar, UnivLevelParam
from ..declaration import ConstructorDeclaration, Declaration, InductiveDeclaration


class OptionDeclaration(Enum):
    """Inductive declaration for optional values."""

    OPTION_DECLARATION = InductiveDeclaration(
        name="Option",
        level_params=("u",),
        type=EPi("A", ESort(UnivLevelParam("u")), ESort(UnivLevelParam("u"))),
        constructor_names=("Option.none", "Option.some"),
    )

    OPTION_NONE_DECLARATION = ConstructorDeclaration(
        name="Option.none",
        level_params=("u",),
        inductive_name="Option",
        type=EPi(
            "A",
            ESort(UnivLevelParam("u")),
            EApp(EConst("Option", (UnivLevelParam("u"),)), EVar("A")),
        ),
    )

    OPTION_SOME_DECLARATION = ConstructorDeclaration(
        name="Option.some",
        level_params=("u",),
        inductive_name="Option",
        type=EPi(
            "A",
            ESort(UnivLevelParam("u")),
            EPi(
                "value",
                EVar("A"),
                EApp(EConst("Option", (UnivLevelParam("u"),)), EVar("A")),
            ),
        ),
    )

    @property
    def declaration(self) -> Declaration:
        """Return the underlying declaration."""
        return self.value
