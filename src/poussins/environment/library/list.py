"""List declarations."""
from __future__ import annotations

from enum import Enum

from ...ast import EApp, EConst, EPi, ESort, EVar, UnivLevelParam
from ..declaration import (
    ConstructorDeclaration,
    Declaration,
    InductiveDeclaration,
    RecursorDeclaration,
)


class ListDeclaration(Enum):
    """Inductive declaration for lists."""

    LIST_DECLARATION = InductiveDeclaration(
        name="List",
        level_params=("u",),
        type=EPi("A", ESort(UnivLevelParam("u")), ESort(UnivLevelParam("u"))),
        constructor_names=("List.nil", "List.cons"),
        recursor_names=("List.rec",)
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

    LIST_REC_DECLARATION = RecursorDeclaration(
        name="List.rec",
        level_params=("u", "v"),
        inductive_name="List",
        num_params=1,
        num_indices=0,
        num_minors=2,
        type=EPi(
            "A", ESort(UnivLevelParam("u")),
            EPi(
                "motive",
                EPi(
                    "_",
                    EApp(EConst("List", (UnivLevelParam("u"),)), EVar("A")),
                    ESort(UnivLevelParam("v"))
                ),
                EPi(
                    "nil",
                    EApp(
                        EVar("motive"),
                        EApp(EConst("List.nil", (UnivLevelParam("u"),)), EVar("A"))
                    ),
                    EPi(
                        "cons",
                        EPi("head", EVar("A"),
                            EPi(
                                "tail",
                                EApp(
                                    EConst("List", (UnivLevelParam("u"),)),
                                    EVar("A")
                                ),
                                EPi("ih", EApp(EVar("motive"), EVar("tail")),
                                    EApp(
                                        EVar("motive"),
                                        EApp(
                                            EApp(
                                                EApp(
                                                    EConst(
                                                        "List.cons",
                                                        (UnivLevelParam("u"),)
                                                    ),
                                                    EVar("A")),
                                                EVar("head"),
                                            ),
                                            EVar("tail"),
                                        ),
                                    ),
                                ),
                            ),
                        ),
                        EPi(
                            "xs",
                            EApp(EConst("List", (UnivLevelParam("u"),)), EVar("A")),
                            EApp(EVar("motive"), EVar("xs")),
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
