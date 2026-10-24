"""Direct-product declarations."""
from __future__ import annotations

from enum import Enum

from ...ast import EApp, EConst, EPi, ESort, EVar, UnivLevelParam
from ..declaration import (
    ConstructorDeclaration,
    Declaration,
    InductiveDeclaration,
    RecursorDeclaration,
)


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
        recursor_names=("Prod.rec",),
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

    PROD_REC_DECLARATION = RecursorDeclaration(
        name="Prod.rec",
        level_params=("u", "v"),
        inductive_name="Prod",
        num_params=2,
        num_indices=0,
        num_minors=1,
        type=EPi(
            "A", ESort(UnivLevelParam("u")),
            EPi("B", ESort(UnivLevelParam("u")),
                EPi(
                    "motive",
                    EPi(
                        "_",
                        EApp(
                            EApp(
                                EConst("Prod", (UnivLevelParam("u"),)),
                                EVar("A")
                            ),
                            EVar("B")
                        ),
                        ESort(UnivLevelParam("v"))
                    ),
                    EPi(
                        "mk",
                        EPi("fst", EVar("A"),
                            EPi("snd", EVar("B"),
                                EApp(
                                    EVar("motive"),
                                    EApp(
                                        EApp(
                                            EApp(
                                                EApp(
                                                    EConst(
                                                        "Prod.mk",
                                                        (UnivLevelParam("u"),)
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
                            "p",
                            EApp(
                                EApp(EConst("Prod", (UnivLevelParam("u"),)), EVar("A")),
                                EVar("B")
                            ),
                            EApp(EVar("motive"), EVar("p")),
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
