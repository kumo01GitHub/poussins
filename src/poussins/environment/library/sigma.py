"""Dependent-pair declarations."""
from __future__ import annotations

from enum import Enum

from ...ast import EApp, EConst, EPi, ESort, EVar, UnivLevelIMax, UnivLevelParam
from ..declaration import ConstructorDeclaration, Declaration, InductiveDeclaration


class SigmaDeclaration(Enum):
    """Inductive declaration for dependent pairs."""

    SIGMA_DECLARATION = InductiveDeclaration(
        name="Sigma",
        level_params=("u", "v"),
        type=EPi(
            "A",
            ESort(UnivLevelParam("u")),
            EPi(
                "B",
                EPi("_", EVar("A"), ESort(UnivLevelParam("v"))),
                ESort(UnivLevelIMax(UnivLevelParam("u"), UnivLevelParam("v"))),
            ),
        ),
        constructor_names=("Sigma.mk",),
    )

    SIGMA_MK_DECLARATION = ConstructorDeclaration(
        name="Sigma.mk",
        level_params=("u", "v"),
        inductive_name="Sigma",
        type=EPi(
            "A",
            ESort(UnivLevelParam("u")),
            EPi(
                "B",
                EPi("_", EVar("A"), ESort(UnivLevelParam("v"))),
                EPi(
                    "fst",
                    EVar("A"),
                    EPi(
                        "snd",
                        EApp(EVar("B"), EVar("fst")),
                        EApp(
                            EApp(
                                EConst(
                                    "Sigma",
                                    (UnivLevelParam("u"), UnivLevelParam("v")),
                                ),
                                EVar("A"),
                            ),
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
