"""Equality declarations."""
from __future__ import annotations

from enum import Enum

from ...ast import EApp, EConst, EPi, ESort, EVar, UnivLevelParam
from ..declaration import (
    ConstructorDeclaration,
    Declaration,
    InductiveDeclaration,
    RecursorDeclaration,
)
from .sort import Sort


class EqualityDeclaration(Enum):
    """Inductive declaration for propositional equality."""

    """Eq inductive declaration for propositional equality."""
    EQ_DECLARATION = InductiveDeclaration(
        name="Eq",
        level_params=(),
        type=EPi(
            "A", Sort.TYPE.sort,
            EPi("x", EVar("A"), EPi("y", EVar("A"), Sort.PROP.sort))
        ),
        constructor_names=("Eq.refl",),
    )

    """Eq.refl constructor declaration for propositional equality."""
    EQ_REFL_DECLARATION = ConstructorDeclaration(
        name="Eq.refl",
        level_params=(),
        inductive_name="Eq",
        type=EPi(
            "A",
            Sort.TYPE.sort,
            EPi(
                "x",
                EVar("A"),
                EApp(EApp(EApp(EConst("Eq", ()), EVar("A")), EVar("x")), EVar("x")),
            ),
        ),
    )

    """Eq.rec recursor declaration for propositional equality."""
    EQ_REC_DECLARATION = RecursorDeclaration(
        name="Eq.rec",
        level_params=("u",),
        inductive_name="Eq",
        num_params=2,
        num_indices=1,
        num_minors=1,
        type=EPi("A", Sort.TYPE.sort,
            EPi("x", EVar("A"),
                EPi("motive", EPi("y", EVar("A"), EPi("h",
                    EApp(EApp(EApp(EConst("Eq", ()), EVar("A")), EVar("x")), EVar("y")),
                    ESort(UnivLevelParam("u")))),
                    EPi("minor", EApp(EApp(EVar("motive"), EVar("x")),
                        EApp(EApp(EConst("Eq.refl", ()), EVar("A")), EVar("x"))),
                        EPi("y", EVar("A"),
                            EPi("h", EApp(EApp(EApp(EConst("Eq", ()), EVar("A")),
                                EVar("x")), EVar("y")),
                                EApp(EApp(EVar("motive"), EVar("y")), EVar("h"))
                            )
                        )
                    )
                )
            )
        )
    )

    @property
    def declaration(self) -> Declaration:
        """Return the underlying declaration."""
        return self.value
