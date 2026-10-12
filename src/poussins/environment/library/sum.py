"""Sum-type declarations."""
from __future__ import annotations

from enum import Enum

from ...ast import EApp, EConst, EPi, ESort, EVar, UnivLevelParam
from ..declaration import (
    ConstructorDeclaration,
    Declaration,
    InductiveDeclaration,
    RecursorDeclaration,
)


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

    SUM_REC_DECLARATION = RecursorDeclaration(
        name="Sum.rec",
        level_params=("u", "v"),
        inductive_name="Sum",
        num_params=2,
        num_indices=0,
        num_minors=2,
        type=EPi(
            "A", ESort(UnivLevelParam("u")),
            EPi(
                "B",
                ESort(UnivLevelParam("u")),
                EPi(
                    "motive",
                    EPi(
                        "_",
                        EApp(
                            EApp(
                                EConst("Sum", (UnivLevelParam("u"),)),
                                EVar("A"),
                            ),
                            EVar("B"),
                        ),
                        ESort(UnivLevelParam("v")),
                    ),
                    EPi(
                        "inl",
                        EPi(
                            "value",
                            EVar("A"),
                            EApp(
                                EVar("motive"),
                                EApp(
                                    EApp(
                                        EApp(
                                            EConst("Sum.inl", (UnivLevelParam("u"),)),
                                            EVar("A"),
                                        ),
                                        EVar("B"),
                                    ),
                                    EVar("value"),
                                ),
                            ),
                        ),
                        EPi(
                            "inr",
                            EPi(
                                "value",
                                EVar("B"),
                                EApp(
                                    EVar("motive"),
                                    EApp(
                                        EApp(
                                            EApp(
                                                EConst(
                                                    "Sum.inr",
                                                    (UnivLevelParam("u"),)
                                                ),
                                                EVar("A"),
                                            ),
                                            EVar("B"),
                                        ),
                                        EVar("value"),
                                    ),
                                ),
                            ),
                            EPi(
                                "s",
                                EApp(
                                    EApp(
                                        EConst("Sum", (UnivLevelParam("u"),)),
                                        EVar("A"),
                                    ),
                                    EVar("B"),
                                ),
                                EApp(EVar("motive"), EVar("s")),
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
