"""Natural numbers declarations."""
from __future__ import annotations

from enum import Enum

from ...ast import (
    EApp,
    EConst,
    ELam,
    EMatch,
    EPi,
    ESort,
    EVar,
    Sort,
    UnivLevelParam,
    UnivLevelSucc,
    UnivLevelZero,
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

    NAT_DECLARATION = InductiveDeclaration(
        name="Nat",
        level_params=(),
        type=Sort.TYPE.sort,
        constructor_names=("Nat.zero", "Nat.succ"),
        recursor_names=("Nat.rec",),
    )

    NAT_ZERO_DECLARATION = ConstructorDeclaration(
        name="Nat.zero",
        level_params=(),
        inductive_name="Nat",
        type=EConst("Nat", ()),
    )

    NAT_SUCC_DECLARATION = ConstructorDeclaration(
        name="Nat.succ",
        level_params=(),
        inductive_name="Nat",
        type=EPi("n", EConst("Nat", ()), EConst("Nat", ())),
    )

    NAT_REC_DECLARATION = RecursorDeclaration(
        name="Nat.rec",
        level_params=("u",),
        inductive_name="Nat",
        num_params=0,
        num_indices=0,
        num_minors=2,
        type=EPi(
            "motive",
            EPi("_", EConst("Nat", ()), ESort(UnivLevelParam("u"))),
            EPi(
                "zero_case",
                EApp(EVar("motive"), EConst("Nat.zero", ())),
                EPi(
                    "succ_case",
                    EPi(
                        "n",
                        EConst("Nat", ()),
                        EPi(
                            "ih",
                            EApp(EVar("motive"), EVar("n")),
                            EApp(
                                EVar("motive"),
                                EApp(EConst("Nat.succ", ()), EVar("n")),
                            ),
                        ),
                    ),
                    EPi(
                        "k",
                        EConst("Nat", ()),
                        EApp(EVar("motive"), EVar("k")),
                    ),
                ),
            ),
        ),
    )

    NAT_ADD_DECLARATION = DefinitionDeclaration(
        name="Nat.add",
        level_params=(),
        type=EPi(
            "n",
            EConst("Nat", ()),
            EPi("m", EConst("Nat", ()), EConst("Nat", ())),
        ),
        value=ELam(
            "n",
            EConst("Nat", ()),
            ELam(
                "m",
                EConst("Nat", ()),
                EApp(
                    EApp(
                        EApp(
                            EApp(
                                EConst("Nat.rec", (UnivLevelSucc(UnivLevelZero()),)),
                                ELam("_", EConst("Nat", ()), EConst("Nat", ())),
                            ),
                            EVar("m"),
                        ),
                        ELam(
                            "n",
                            EConst("Nat", ()),
                            ELam(
                                "ih",
                                EConst("Nat", ()),
                                EApp(EConst("Nat.succ", ()), EVar("ih")),
                            ),
                        ),
                    ),
                    EVar("n"),
                ),
            ),
        ),
    )

    NAT_SUB_DECLARATION = DefinitionDeclaration(
        name="Nat.sub",
        level_params=(),
        type=EPi(
            "n",
            EConst("Nat", ()),
            EPi("m", EConst("Nat", ()), EConst("Nat", ())),
        ),
        value=ELam(
            "n",
            EConst("Nat", ()),
            ELam(
                "m",
                EConst("Nat", ()),
                EApp(
                    EApp(
                        EApp(
                            EApp(
                                EConst("Nat.rec", (UnivLevelSucc(UnivLevelZero()),)),
                                ELam("_", EConst("Nat", ()), EConst("Nat", ())),
                            ),
                            EVar("n"),
                        ),
                        ELam(
                            "m",
                            EConst("Nat", ()),
                            ELam(
                                "ih",
                                EConst("Nat", ()),
                                EApp(
                                    EApp(
                                        EApp(
                                            EApp(
                                                EConst(
                                                    "Nat.rec",
                                                    (UnivLevelSucc(UnivLevelZero(),),),
                                                ),
                                                ELam(
                                                    "_",
                                                    EConst("Nat", ()),
                                                    EConst("Nat", ()),
                                                ),
                                            ),
                                            EConst("Nat.zero", ()),
                                        ),
                                        ELam(
                                            "k",
                                            EConst("Nat", ()),
                                            ELam(
                                                "_",
                                                EConst("Nat", ()),
                                                EVar("k"),
                                            ),
                                        ),
                                    ),
                                    EVar("ih"),
                                ),
                            ),
                        ),
                    ),
                    EVar("m"),
                ),
            ),
        ),
    )

    NAT_MUL_DECLARATION = DefinitionDeclaration(
        name="Nat.mul",
        level_params=(),
        type=EPi(
            "n",
            EConst("Nat", ()),
            EPi("m", EConst("Nat", ()), EConst("Nat", ())),
        ),
        value=ELam(
            "n",
            EConst("Nat", ()),
            ELam(
                "m",
                EConst("Nat", ()),
                EApp(
                    EApp(
                        EApp(
                            EApp(
                                EConst("Nat.rec", (UnivLevelSucc(UnivLevelZero()),)),
                                ELam("_", EConst("Nat", ()), EConst("Nat", ())),
                            ),
                            EConst("Nat.zero", ()),
                        ),
                        ELam(
                            "n",
                            EConst("Nat", ()),
                            ELam(
                                "ih",
                                EConst("Nat", ()),
                                EApp(
                                    EApp(
                                        EConst("Nat.add", ()),
                                        EVar("ih"),
                                    ),
                                    EVar("m"),
                                ),
                            ),
                        ),
                    ),
                    EVar("n"),
                ),
            ),
        ),
    )

    NAT_MOD_DECLARATION = DefinitionDeclaration(
        name="Nat.mod",
        level_params=(),
        type=EPi(
            "n",
            EConst("Nat", ()),
            EPi("m", EConst("Nat", ()), EConst("Nat", ())),
        ),
        value=ELam(
            "n",
            EConst("Nat", ()),
            ELam(
                "m",
                EConst("Nat", ()),
                EApp(
                    EApp(
                        EApp(
                            EApp(
                                EConst("Nat.rec", (UnivLevelSucc(UnivLevelZero()),)),
                                ELam("_", EConst("Nat", ()), EConst("Nat", ())),
                            ),
                            EConst("Nat.zero", ()),
                        ),
                        ELam(
                            "n_ih",
                            EConst("Nat", ()),
                            ELam(
                                "ih",
                                EConst("Nat", ()),
                                EMatch(
                                    inductive_name="Nat",
                                    discriminee=EApp(
                                        EApp(
                                            EConst("Nat.sub", ()),
                                            EVar("m"),
                                        ),
                                        EApp(EConst("Nat.succ", ()), EVar("ih")),
                                    ),
                                    motive=ELam("_", EConst("Nat", ()), EConst("Nat", ())),
                                    cases=(
                                        EConst("Nat.zero", ()),
                                        ELam(
                                            "k",
                                            EConst("Nat", ()),
                                            EApp(EConst("Nat.succ", ()), EVar("ih")),
                                        ),
                                    ),
                                ),
                            ),
                        ),
                    ),
                    EVar("n"),
                ),
            ),
        ),
    )

    NAT_DIV_DECLARATION = DefinitionDeclaration(
        name="Nat.div",
        level_params=(),
        type=EPi(
            "n",
            EConst("Nat", ()),
            EPi("m", EConst("Nat", ()), EConst("Nat", ())),
        ),
        value=ELam(
            "n",
            EConst("Nat", ()),
            ELam(
                "m",
                EConst("Nat", ()),
                EApp(
                    EApp(
                        EApp(
                            EApp(
                                EConst("Nat.rec", (UnivLevelSucc(UnivLevelZero()),)),
                                ELam("_", EConst("Nat", ()), EConst("Nat", ())),
                            ),
                            EConst("Nat.zero", ()),
                        ),
                        ELam(
                            "n_ih",
                            EConst("Nat", ()),
                            ELam(
                                "ih",
                                EConst("Nat", ()),
                                EMatch(
                                    inductive_name="Nat",
                                    discriminee=EApp(
                                        EApp(
                                            EConst("Nat.sub", ()),
                                            EVar("m"),
                                        ),
                                        EApp(
                                            EConst("Nat.succ", ()),
                                            EApp(
                                                EApp(
                                                    EApp(
                                                        EApp(
                                                            EConst("Nat.rec", (UnivLevelSucc(UnivLevelZero()),)),
                                                            ELam("_", EConst("Nat", ()), EConst("Nat", ())),
                                                        ),
                                                        EConst("Nat.zero", ()),
                                                    ),
                                                    ELam(
                                                        "n_ih2",
                                                        EConst("Nat", ()),
                                                        ELam(
                                                            "ih2",
                                                            EConst("Nat", ()),
                                                            EMatch(
                                                                inductive_name="Nat",
                                                                discriminee=EApp(
                                                                    EApp(
                                                                        EConst(
                                                                            "Nat.sub",
                                                                            ()
                                                                        ),
                                                                        EVar("m"),
                                                                    ),
                                                                    EApp(
                                                                        EConst("Nat.succ", ()),
                                                                        EVar("ih2"),
                                                                    ),
                                                                ),
                                                                motive=ELam(
                                                                    "_",
                                                                    EConst("Nat", ()),
                                                                    EConst("Nat", ())
                                                                ),
                                                                cases=(
                                                                    EConst(
                                                                        "Nat.zero",
                                                                        ()
                                                                    ),
                                                                    ELam(
                                                                        "k",
                                                                        EConst("Nat", ()),
                                                                        EApp(
                                                                            EConst("Nat.succ", ()),
                                                                            EVar("ih2"),
                                                                        )
                                                                    ),
                                                                ),
                                                            ),
                                                        ),
                                                    ),
                                                ),
                                                EVar("n_ih"),
                                            ),
                                        ),
                                    ),
                                    motive=ELam(
                                        "_",
                                        EConst("Nat", ()),
                                        EConst("Nat", ())
                                    ),
                                    cases=(
                                        EApp(EConst("Nat.succ", ()), EVar("ih")),
                                        ELam("k", EConst("Nat", ()), EVar("ih")),
                                    ),
                                ),
                            ),
                        ),
                    ),
                    EVar("n"),
                ),
            ),
        ),
    )

    @property
    def declaration(self) -> Declaration:
        """Return the underlying declaration."""
        return self.value
