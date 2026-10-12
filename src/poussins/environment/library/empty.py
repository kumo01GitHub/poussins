"""Empty declarations."""
from __future__ import annotations

from enum import Enum

from ...ast import EApp, EConst, EPi, ESort, EVar, UnivLevelParam
from ..declaration import Declaration, InductiveDeclaration, RecursorDeclaration
from .sort import Sort


class EmptyDeclaration(Enum):
    """Inductive declaration for Empty."""

    EMPTY_DECLARATION = InductiveDeclaration(
        name="Empty",
        level_params=(),
        type=Sort.TYPE.sort,
        constructor_names=(),
    )

    """Empty.rec recursor declaration (Principle of Explosion)."""
    EMPTY_REC_DECLARATION = RecursorDeclaration(
        name="Empty.rec",
        level_params=("u",),
        inductive_name="Empty",
        num_params=0,
        num_indices=0,
        num_minors=0,
        type=EPi(
            "motive",
            EPi("_", EConst("Empty", ()), ESort(UnivLevelParam("u"))),
            EPi(
                "t",
                EConst("Empty", ()),
                EApp(EVar("motive"), EVar("t")),
            ),
        ),
    )

    @property
    def declaration(self) -> Declaration:
        """Return the underlying declaration."""
        return self.value
