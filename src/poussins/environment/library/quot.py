"""Quotient-type declarations."""
from __future__ import annotations

from enum import Enum

from ...ast import EApp, EConst, EPi, ESort, EVar, UnivLevelParam
from ..declaration import Declaration, QuotientDeclaration
from .sort import Sort


class QuotDeclaration(Enum):
    """Quotient type former and core primitives."""

    QUOT_DECLARATION = QuotientDeclaration(
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

    QUOT_MK_DECLARATION = QuotientDeclaration(
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
                        EApp(
                            EConst("Quot", (UnivLevelParam("u"),)),
                            EVar("A"),
                        ),
                        EVar("r"),
                    ),
                ),
            ),
        ),
        variant="mk",
    )

    QUOT_LIFT_DECLARATION = QuotientDeclaration(
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
                                        EApp(
                                            EApp(EVar("r"), EVar("x")),
                                            EVar("y"),
                                        ),
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
                                        EConst(
                                            "Quot", (UnivLevelParam("u"),)
                                        ),
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
        variant="lift",
    )

    QUOT_IND_DECLARATION = QuotientDeclaration(
        name="Quot.ind",
        level_params=("u", "v"),
        type=EPi(
            "A",
            ESort(UnivLevelParam("u")),
            EPi(
                "r",
                EPi("x", EVar("A"), EPi("y", EVar("A"), Sort.PROP.sort)),
                EPi(
                    "p",
                    EPi(
                        "q",
                        EApp(
                            EApp(
                                EConst("Quot", (UnivLevelParam("u"),)),
                                EVar("A"),
                            ),
                            EVar("r"),
                        ),
                        ESort(UnivLevelParam("v")),
                    ),
                    EPi(
                        "h",
                        EPi(
                            "a",
                            EVar("A"),
                            EApp(
                                EVar("p"),
                                EApp(
                                    EApp(
                                        EApp(
                                            EConst(
                                                "Quot.mk",
                                                (UnivLevelParam("u"),),
                                            ),
                                            EVar("A"),
                                        ),
                                        EVar("r"),
                                    ),
                                    EVar("a"),
                                ),
                            ),
                        ),
                        EPi(
                            "q",
                            EApp(
                                EApp(
                                    EConst(
                                        "Quot", (UnivLevelParam("u"),)
                                    ),
                                    EVar("A"),
                                ),
                                EVar("r"),
                            ),
                            EApp(EVar("p"), EVar("q")),
                        ),
                    ),
                ),
            ),
        ),
        variant="ind",
    )

    @property
    def declaration(self) -> Declaration:
        """Return the underlying declaration."""
        return self.value
