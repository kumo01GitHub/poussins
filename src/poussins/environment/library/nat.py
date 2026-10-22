"""Natural numbers declarations."""
from __future__ import annotations

from enum import Enum

from ...ast import (
    EApp,
    EConst,
    ELam,
    EPi,
    ESort,
    EVar,
    Sort,
    UnivLevelParam,
)
from ..declaration import (
    ConstructorDeclaration,
    Declaration,
    DefinitionDeclaration,
    InductiveDeclaration,
    RecursorDeclaration,
)


class NatDeclaration(Enum):
    """Inductive declaration for natural numbers."""

    """Nat inductive declaration for natural numbers."""
    NAT_DECLARATION = InductiveDeclaration(
        name="Nat",
        level_params=(),
        type=Sort.TYPE.sort,
        constructor_names=("Nat.zero", "Nat.succ"),
    )

    """Nat.zero constructor declaration for natural numbers."""
    NAT_ZERO_DECLARATION = ConstructorDeclaration(
        name="Nat.zero",
        level_params=(),
        inductive_name="Nat",
        type=EConst("Nat", ()),
    )

    """Nat.succ constructor declaration for natural numbers."""
    NAT_SUCC_DECLARATION = ConstructorDeclaration(
        name="Nat.succ",
        level_params=(),
        inductive_name="Nat",
        type=EPi("n", EConst("Nat", ()), EConst("Nat", ())),
    )

    """Nat.rec recursor declaration for natural numbers."""
    NAT_REC_DECLARATION = RecursorDeclaration(
        name="Nat.rec",
        level_params=("u",),
        inductive_name="Nat",
        num_params=0,
        num_indices=0,
        num_minors=2,
        type=EPi("motive", EPi("_", EConst("Nat", ()), ESort(UnivLevelParam("u"))),
            EPi("zero_case", EApp(EVar("motive"), EConst("Nat.zero", ())),
                EPi("succ_case", EPi("n", EConst("Nat", ()),
                    EPi("ih", EApp(EVar("motive"), EVar("n")), EApp(EVar("motive"),
                        EApp(EConst("Nat.succ", ()), EVar("n"))))),
                    EPi("k", EConst("Nat", ()),
                        EApp(EVar("motive"), EVar("k"))
                    )
                )
            )
        )
    )

    """Nat.add definition declaration for natural numbers."""
    NAT_ADD_DECLARATION = DefinitionDeclaration(
        name="Nat.add",
        level_params=(),
        type=EPi("n", EConst("Nat", ()), EPi("m", EConst("Nat", ()),
            EConst("Nat", ()))),
        value=ELam("n", EConst("Nat", ()), ELam("m", EConst("Nat", ()), EVar("m"))),
    )

    """Nat.sub definition declaration for natural numbers."""
    NAT_SUB_DECLARATION = DefinitionDeclaration(
        name="Nat.sub",
        level_params=(),
        type=EPi(
            "n",
            EConst("Nat", ()),
            EPi("m", EConst("Nat", ()), EConst("Nat", ()))
        ),
        value=ELam("n", EConst("Nat", ()), ELam("m", EConst("Nat", ()), EVar("n"))),
    )

    """Nat.mul definition declaration for natural numbers."""
    NAT_MUL_DECLARATION = DefinitionDeclaration(
        name="Nat.mul",
        level_params=(),
        type=EPi(
            "n",
            EConst("Nat", ()), EPi("m", EConst("Nat", ()),
                EConst("Nat", ()))
        ),
        value=ELam(
            "n",
            EConst("Nat", ()),
            ELam("m", EConst("Nat", ()), EConst("Nat.zero", ()))
        ),
    )

    """Nat.div definition declaration for natural numbers."""
    NAT_DIV_DECLARATION = DefinitionDeclaration(
        name="Nat.div",
        level_params=(),
        type=EPi(
            "n",
            EConst("Nat", ()),
            EPi("m", EConst("Nat", ()), EConst("Nat", ()))
        ),
        value=ELam(
            "n",
            EConst("Nat", ()),
            ELam("m", EConst("Nat", ()), EConst("Nat.zero", ()))
        ),
    )

    """Nat.mod definition declaration for natural numbers."""
    NAT_MOD_DECLARATION = DefinitionDeclaration(
        name="Nat.mod",
        level_params=(),
        type=EPi(
            "n",
            EConst("Nat", ()),
            EPi("m", EConst("Nat", ()), EConst("Nat", ()))
        ),
        value=ELam(
            "n",
            EConst("Nat", ()),
            ELam("m", EConst("Nat", ()), EVar("n"))
        ),
    )

    @property
    def declaration(self) -> Declaration:
        """Return the underlying declaration."""
        return self.value
