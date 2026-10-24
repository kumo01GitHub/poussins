"""Length-indexed vector declarations."""
from __future__ import annotations

from enum import Enum

from ...ast import EApp, EConst, EPi, ESort, EVar, UnivLevelParam
from ..declaration import (
    ConstructorDeclaration,
    Declaration,
    InductiveDeclaration,
    RecursorDeclaration,
)


class VectorDeclaration(Enum):
    """Inductive declaration for vectors."""

    VECTOR_DECLARATION = InductiveDeclaration(
        name="Vector",
        level_params=("u",),
        type=EPi(
            "A",
            ESort(UnivLevelParam("u")),
            EPi("n", EConst("Nat", ()), ESort(UnivLevelParam("u"))),
        ),
        constructor_names=("Vector.nil", "Vector.cons"),
        recursor_names=("Vector.rec",),
    )

    VECTOR_NIL_DECLARATION = ConstructorDeclaration(
        name="Vector.nil",
        level_params=("u",),
        inductive_name="Vector",
        type=EPi(
            "A",
            ESort(UnivLevelParam("u")),
            EApp(
                EApp(EConst("Vector", (UnivLevelParam("u"),)), EVar("A")),
                EConst("Nat.zero", ()),
            ),
        ),
    )

    VECTOR_CONS_DECLARATION = ConstructorDeclaration(
        name="Vector.cons",
        level_params=("u",),
        inductive_name="Vector",
        type=EPi(
            "A",
            ESort(UnivLevelParam("u")),
            EPi(
                "n",
                EConst("Nat", ()),
                EPi(
                    "head",
                    EVar("A"),
                    EPi(
                        "tail",
                        EApp(
                            EApp(EConst("Vector", (UnivLevelParam("u"),)), EVar("A")),
                            EVar("n"),
                        ),
                        EApp(
                            EApp(EConst("Vector", (UnivLevelParam("u"),)), EVar("A")),
                            EApp(EConst("Nat.succ", ()), EVar("n")),
                        ),
                    ),
                ),
            ),
        ),
    )

    VECTOR_REC_DECLARATION = RecursorDeclaration(
        name="Vector.rec",
        level_params=("u", "v"),
        inductive_name="Vector",
        num_params=1,
        num_indices=1,
        num_minors=2,
        type=EPi(
            "A", ESort(UnivLevelParam("u")),
            EPi(
                "motive",
                EPi(
                    "n", EConst("Nat", ()),
                    EPi(
                        "_",
                        EApp(
                            EApp(EConst("Vector", (UnivLevelParam("u"),)), EVar("A")),
                            EVar("n")
                        ),
                        ESort(UnivLevelParam("v"))
                    ),
                ),
                EPi(
                    "nil",
                    EApp(
                        EApp(
                            EVar("motive"),
                            EConst("Nat.zero", ()),
                        ),
                        EApp(
                            EConst("Vector.nil", (UnivLevelParam("u"),)),
                            EVar("A"),
                        ),
                    ),
                    EPi(
                        "cons",
                        EPi(
                            "n", EConst("Nat", ()),
                            EPi(
                                "head", EVar("A"),
                                EPi(
                                    "tail",
                                    EApp(
                                        EApp(
                                            EConst("Vector", (UnivLevelParam("u"),)),
                                            EVar("A"),
                                        ),
                                        EVar("n"),
                                    ),
                                    EPi(
                                        "ih",
                                        EApp(
                                            EApp(
                                                EVar("motive"),
                                                EVar("n"),
                                            ),
                                            EVar("tail"),
                                        ),
                                        EApp(
                                            EApp(
                                                EVar("motive"),
                                                EApp(EConst("Nat.succ", ()), EVar("n")),
                                            ),
                                            EApp(
                                                EApp(
                                                    EApp(
                                                        EApp(
                                                            EConst(
                                                                "Vector.cons",
                                                                (UnivLevelParam("u"),)
                                                            ),
                                                            EVar("A"),
                                                        ),
                                                        EVar("n"),
                                                    ),
                                                    EVar("head"),
                                                ),
                                                EVar("tail"),
                                            ),
                                        ),
                                    ),
                                ),
                            ),
                        ),
                        EPi(
                            "n", EConst("Nat", ()),
                            EPi(
                                "v",
                                EApp(
                                    EApp(
                                        EConst("Vector", (UnivLevelParam("u"),)),
                                        EVar("A"),
                                    ),
                                    EVar("n"),
                                ),
                                EApp(
                                    EApp(
                                        EVar("motive"),
                                        EVar("n"),
                                    ),
                                    EVar("v"),
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
