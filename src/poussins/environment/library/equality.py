from __future__ import annotations
from enum import Enum

from .sort import Sort
from ..declaration import ConstructorDeclaration, Declaration, InductiveDeclaration
from ...ast.expr import EConst, EPi, EVar, EApp

class EqualityDeclaration(Enum):
    """
    Inductive declaration for propositional equality.
    """

    """Eq inductive declaration for propositional equality."""
    EQ_DECLARATION = InductiveDeclaration(
        name="Eq",
        level_params=(),
        type=EPi("A", Sort.TYPE.sort, EPi("x", EVar("A"), EPi("y", EVar("A"), Sort.PROP.sort))),
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

    @property
    def declaration(self) -> Declaration:
        """Return the underlying declaration."""
        return self.value
