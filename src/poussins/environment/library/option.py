"""Optional-value declarations."""
from __future__ import annotations

from enum import Enum

from ...ast import EApp, EConst, EPi, ESort, EVar, UnivLevelParam
from ..declaration import (
    ConstructorDeclaration,
    Declaration,
    InductiveDeclaration,
    RecursorDeclaration,
)


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

    OPTION_REC_DECLARATION = RecursorDeclaration(
        name="Option.rec",
        level_params=("u", "v"),
        inductive_name="Option",
        num_params=1,
        num_indices=0,
        num_minors=2,
        type=EPi(
            "A", ESort(UnivLevelParam("u")),
            EPi(
                "motive",
                EPi(
                    "_",
                    EApp(EConst("Option", (UnivLevelParam("u"),)), EVar("A")),
                    ESort(UnivLevelParam("v"))
                ),
                EPi(
                    "none",
                    EApp(
                        EVar("motive"),
                        EApp(
                            EConst("Option.none", (UnivLevelParam("u"),)),
                            EVar("A")
                        )
                    ),
                    EPi(
                        "some",
                        EPi(
                            "value",
                            EVar("A"),
                            EApp(
                                EVar("motive"),
                                EApp(
                                    EApp(
                                        EConst("Option.some", (UnivLevelParam("u"),)),
                                        EVar("A"),
                                    ),
                                    EVar("value"),
                                ),
                            ),
                        ),
                        EPi(
                            "opt",
                            EApp(EConst("Option", (UnivLevelParam("u"),)), EVar("A")),
                            EApp(EVar("motive"), EVar("opt")),
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
