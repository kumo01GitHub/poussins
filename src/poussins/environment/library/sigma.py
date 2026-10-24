"""Dependent-pair declarations."""
from __future__ import annotations

from enum import Enum

from ...ast import EApp, EConst, EPi, ESort, EVar, UnivLevelIMax, UnivLevelParam
from ..declaration import (
    ConstructorDeclaration,
    Declaration,
    InductiveDeclaration,
    RecursorDeclaration,
)


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
        recursor_names=("Sigma.rec",),
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

    SIGMA_REC_DECLARATION = RecursorDeclaration(
        name="Sigma.rec",
        level_params=("u", "v", "w"),
        inductive_name="Sigma",
        num_params=2,
        num_indices=0,
        num_minors=1,
        type=EPi(
            "A", ESort(UnivLevelParam("u")),
            EPi("B", EPi("_", EVar("A"), ESort(UnivLevelParam("v"))),
                EPi(
                    "motive",
                    EPi(
                        "_",
                        EApp(
                            EApp(
                                EConst(
                                    "Sigma",
                                    (
                                        UnivLevelParam("u"),
                                        UnivLevelParam("v")
                                    )
                                ),
                                EVar("A")
                            ),
                            EVar("B")
                        ),
                        ESort(UnivLevelParam("w"))
                    ),
                    EPi(
                        "mk",
                        EPi("fst", EVar("A"),
                            EPi("snd", EApp(EVar("B"), EVar("fst")),
                                EApp(
                                    EVar("motive"),
                                    EApp(
                                        EApp(
                                            EApp(
                                                EApp(
                                                    EConst(
                                                        "Sigma.mk",
                                                        (
                                                            UnivLevelParam("u"),
                                                            UnivLevelParam("v")
                                                        )
                                                    ),
                                                    EVar("A")
                                                ),
                                                EVar("B"),
                                            ),
                                            EVar("fst"),
                                        ),
                                        EVar("snd"),
                                    ),
                                ),
                            ),
                        ),
                        EPi(
                            "s",
                            EApp(
                                EApp(
                                    EConst(
                                        "Sigma",
                                        (UnivLevelParam("u"), UnivLevelParam("v"))
                                    ),
                                    EVar("A")
                                ),
                                EVar("B")
                            ),
                            EApp(EVar("motive"), EVar("s")),
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
