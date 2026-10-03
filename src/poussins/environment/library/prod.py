"""Direct-product declarations."""
from __future__ import annotations

from enum import Enum

from ...ast import EApp, EConst, EPi, ESort, EVar, UnivLevelParam
from ..declaration import ConstructorDeclaration, Declaration, InductiveDeclaration


class ProdDeclaration(Enum):
    """Inductive declaration for direct products."""

    PROD_DECLARATION = InductiveDeclaration(
        name="Prod",
        level_params=("u",),
        type=EPi(
            "A",
            ESort(UnivLevelParam("u")),
            EPi("B", ESort(UnivLevelParam("u")), ESort(UnivLevelParam("u"))),
        ),
        constructor_names=("Prod.mk",),
    )

    PROD_MK_DECLARATION = ConstructorDeclaration(
        name="Prod.mk",
        level_params=("u",),
        inductive_name="Prod",
        type=EPi(
            "A",
            ESort(UnivLevelParam("u")),
            EPi(
                "B",
                ESort(UnivLevelParam("u")),
                EPi(
                    "fst",
                    EVar("A"),
                    EPi(
                        "snd",
                        EVar("B"),
                        EApp(
                            EApp(EConst("Prod", (UnivLevelParam("u"),)), EVar("A")),
                            EVar("B"),
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
