"""Quotient-type declarations."""
from __future__ import annotations

from enum import Enum

from ...ast import EApp, EConst, EPi, ESort, EVar, UnivLevelParam
from ..declaration import AxiomDeclaration, Declaration, QuotientDeclaration
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
                EPi(
                    "x",
                    EVar("A"),
                    EPi("y", EVar("A"), Sort.PROP.sort),
                ),
                ESort(UnivLevelParam("u")),
            ),
        ),
        variant="quot",
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

    QUOT_SOUND_DECLARATION = AxiomDeclaration(
        name="Quot.sound",
        level_params=("u",),
        type=EPi(
            "A", ESort(UnivLevelParam("u")),
            EPi(
                "r", EPi("x", EVar("A"), EPi("y", EVar("A"), Sort.PROP.sort)),
                EPi(
                    "a", EVar("A"),
                    EPi(
                        "b", EVar("A"),
                        EPi(
                            "h", EApp(EApp(EVar("r"), EVar("a")), EVar("b")),
                            EApp(
                                EApp(
                                    EApp(
                                        EConst("Eq", (UnivLevelParam("u"),)),
                                        EApp(
                                            EApp(
                                                EConst("Quot", (UnivLevelParam("u"),)),
                                                EVar("A")
                                            ),
                                            EVar("r")
                                        )
                                    ),
                                    EApp(
                                        EApp(
                                            EApp(
                                                EConst(
                                                    "Quot.mk",
                                                    (UnivLevelParam("u"),)
                                                ),
                                                EVar("A")
                                            ),
                                            EVar("r")
                                        ),
                                        EVar("a")
                                    ),
                                ),
                                EApp(
                                    EApp(
                                        EApp(
                                            EConst("Quot.mk", (UnivLevelParam("u"),)),
                                            EVar("A")
                                        ),
                                        EVar("r")
                                    ),
                                    EVar("b")
                                ),
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
