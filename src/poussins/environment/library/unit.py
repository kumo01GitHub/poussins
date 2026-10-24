"""Unit declarations."""
from __future__ import annotations

from enum import Enum

from ...ast import EApp, EConst, EPi, ESort, EVar, Sort, UnivLevelParam
from ..declaration import (
    ConstructorDeclaration,
    Declaration,
    InductiveDeclaration,
    RecursorDeclaration,
)


class UnitDeclaration(Enum):
    """Inductive declaration for Unit."""

    UNIT_DECLARATION = InductiveDeclaration(
        name="Unit",
        level_params=(),
        type=Sort.TYPE.sort,
        constructor_names=("Unit.unit",),
        recursor_names=("Unit.rec",),
    )

    UNIT_UNIT_DECLARATION = ConstructorDeclaration(
        name="Unit.unit",
        level_params=(),
        inductive_name="Unit",
        type=EConst("Unit", ()),
    )

    """Unit.rec recursor declaration."""
    UNIT_REC_DECLARATION = RecursorDeclaration(
        name="Unit.rec",
        level_params=("u",),
        inductive_name="Unit",
        num_params=0,
        num_indices=0,
        num_minors=1,
        type=EPi(
            "motive",
            EPi("_", EConst("Unit", ()), ESort(UnivLevelParam("u"))),
            EPi(
                "minor",
                EApp(EVar("motive"), EConst("Unit.unit", ())),
                EPi(
                    "t",
                    EConst("Unit", ()),
                    EApp(EVar("motive"), EVar("t")),
                ),
            ),
        ),
    )

    @property
    def declaration(self) -> Declaration:
        """Return the underlying declaration."""
        return self.value
