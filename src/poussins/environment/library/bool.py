"""Boolean declarations."""
from __future__ import annotations

from enum import Enum

from ...ast.expr import EApp, EConst, EPi, ESort, EVar
from ...ast.universe import UnivLevelParam
from ..declaration import (
    ConstructorDeclaration,
    Declaration,
    InductiveDeclaration,
    RecursorDeclaration,
)
from .sort import Sort


class BoolDeclaration(Enum):
    """Inductive declaration for booleans."""

    """Bool inductive declaration for booleans."""
    BOOL_DECLARATION = InductiveDeclaration(
        name="Bool",
        level_params=(),
        type=Sort.TYPE.sort,
        constructor_names=("Bool.true", "Bool.false"),
    )

    """Bool.true constructor declaration for booleans."""
    BOOL_TRUE_DECLARATION = ConstructorDeclaration(
        name="Bool.true",
        level_params=(),
        inductive_name="Bool",
        type=EConst("Bool", ()),
    )

    """Bool.false constructor declaration for booleans."""
    BOOL_FALSE_DECLARATION = ConstructorDeclaration(
        name="Bool.false",
        level_params=(),
        inductive_name="Bool",
        type=EConst("Bool", ()),
    )

    """Bool.rec recursor declaration for booleans."""
    BOOL_REC_DECLARATION = RecursorDeclaration(
        name="Bool.rec",
        level_params=("u",),
        type=EPi(
            var="motive",
            domain=EPi(
                var="_",
                domain=EConst("Bool", ()),
                body=ESort(UnivLevelParam("u"))
            ),
            body=EPi(
                var="t_case",
                domain=EApp(EVar("motive"), EConst("Bool.true", ())),
                body=EPi(
                    var="f_case",
                    domain=EApp(EVar("motive"), EConst("Bool.false", ())),
                    body=EPi(
                        var="b",
                        domain=EConst("Bool", ()),
                        body=EApp(EVar("motive"), EVar("b"))
                    )
                )
            )
        ),
        inductive_name="Bool",
        num_params=0,
        num_indices=0,
        num_minors=2,
    )

    @property
    def declaration(self) -> Declaration:
        """Return the underlying declaration."""
        return self.value
