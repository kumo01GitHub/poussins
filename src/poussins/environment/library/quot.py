"""Quotient-type declarations."""
from __future__ import annotations

from enum import Enum

from ...ast import EApp, EConst, EPi, ESort, EVar, UnivLevelParam
from ..declaration import AxiomDeclaration, Declaration, QuotDeclaration
from .sort import Sort


class QuotLibraryDeclaration(Enum):
    """Quotient type former and core axioms."""

    QUOT_DECLARATION = QuotDeclaration(
        name="Quot",
        level_params=("u",),
        type=EPi(
            "A",
            ESort(UnivLevelParam("u")),
            EPi(
                "r",
                EPi("x", EVar("A"), EPi("y", EVar("A"), Sort.PROP.sort)),
                ESort(UnivLevelParam("u")),
            ),
        ),
        variant="type",
    )

    QUOT_MK_DECLARATION = AxiomDeclaration(
        name="Quot.mk",
        level_params=("u",),
        type=EPi(
            "A",
            ESort(UnivLevelParam("u")),
            EPi(
                "r",
                EPi("x", EVar("A"), EPi("y", EVar("A"), Sort.PROP.sort)),
                EPi(
                    "x",
                    EVar("A"),
                    EApp(
                        EApp(EConst("Quot", (UnivLevelParam("u"),)), EVar("A")),
                        EVar("r"),
                    ),
                ),
            ),
        ),
    )

    QUOT_LIFT_DECLARATION = AxiomDeclaration(
        name="Quot.lift",
        level_params=("u", "v"),
        type=EPi(
            "A",
            ESort(UnivLevelParam("u")),
            EPi(
                "r",
                EPi("x", EVar("A"), EPi("y", EVar("A"), Sort.PROP.sort)),
                EPi(
                    "B",
                    ESort(UnivLevelParam("v")),
                    EPi(
                        "f",
                        EPi("x", EVar("A"), EVar("B")),
                        EPi(
                            "h",
                            EPi(
                                "x",
                                EVar("A"),
                                EPi(
                                    "y",
                                    EVar("A"),
                                    EPi(
                                        "hr",
                                        EApp(EApp(EVar("r"), EVar("x")), EVar("y")),
                                        EApp(
                                            EApp(
                                                EApp(EConst("Eq", ()), EVar("B")),
                                                EApp(EVar("f"), EVar("x")),
                                            ),
                                            EApp(EVar("f"), EVar("y")),
                                        ),
                                    ),
                                ),
                            ),
                            EPi(
                                "q",
                                EApp(
                                    EApp(
                                        EConst("Quot", (UnivLevelParam("u"),)),
                                        EVar("A"),
                                    ),
                                    EVar("r"),
                                ),
                                EVar("B"),
                            ),
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
