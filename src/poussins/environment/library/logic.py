""""Standard logical declarations."""
from __future__ import annotations

from enum import Enum

from ...ast import EApp, EConst, ELam, EPi, ESort, EVar, UnivLevelParam
from ..declaration import (
    ConstructorDeclaration,
    Declaration,
    DefinitionDeclaration,
    InductiveDeclaration,
    RecursorDeclaration,
)
from .sort import Sort


class LogicDeclaration(Enum):
    """Standard logical declarations for propositions and connectives."""

    """True (⊤) inductive declaration for logical truth."""
    TRUE_DECLARATION = InductiveDeclaration(
        name="True",
        level_params=(),
        type=Sort.PROP.sort,
        constructor_names=("True.intro",),
    )

    """True.intro constructor declaration for logical truth."""
    TRUE_INTRO_DECLARATION = ConstructorDeclaration(
        name="True.intro",
        level_params=(),
        inductive_name="True",
        type=EConst("True", ()),
    )

    """True.rec recursor declaration."""
    TRUE_REC_DECLARATION = RecursorDeclaration(
        name="True.rec",
        level_params=("u",),
        inductive_name="True",
        num_params=0,
        num_indices=0,
        num_minors=1,
        type=EPi("motive", EPi("_", EConst("True", ()), ESort(UnivLevelParam("u"))),
            EPi("minor", EApp(EVar("motive"), EConst("True.intro", ())),
                EPi("t", EConst("True", ()),
                    EApp(EVar("motive"), EVar("t"))
                )
            )
        )
    )

    """False (⊥) inductive declaration for logical falsehood."""
    FALSE_DECLARATION = InductiveDeclaration(
        name="False",
        level_params=(),
        type=Sort.PROP.sort,
        constructor_names=(),
    )

    """False.rec recursor declaration for logical falsehood (Principle of Explosion)."""
    FALSE_REC_DECLARATION = RecursorDeclaration(
        name="False.rec",
        level_params=("u",),
        inductive_name="False",
        num_params=0,
        num_indices=0,
        num_minors=0,
        type=EPi("motive", EPi("_", EConst("False", ()), ESort(UnivLevelParam("u"))),
            EPi("t", EConst("False", ()),
                EApp(EVar("motive"), EVar("t"))
            )
        )
    )

    """And (∧) inductive declaration for logical conjunction."""
    AND_DECLARATION = InductiveDeclaration(
        name="And",
        level_params=(),
        type=EPi("A", Sort.PROP.sort, EPi("B", Sort.PROP.sort, Sort.PROP.sort)),
        constructor_names=("And.intro",),
    )

    """And.intro constructor declaration for logical conjunction."""
    AND_INTRO_DECLARATION = ConstructorDeclaration(
        name="And.intro",
        level_params=(),
        inductive_name="And",
        type=EPi("A", Sort.PROP.sort, EPi("B", Sort.PROP.sort,
            EPi("hA", EVar("A"), EPi("hB", EVar("B"),
                EApp(EApp(EConst("And", ()), EVar("A")), EVar("B")),
            ),),
        ),),
    )

    """And.rec recursor declaration (Conjunction Elimination)."""
    AND_REC_DECLARATION = RecursorDeclaration(
        name="And.rec",
        level_params=("u",),
        inductive_name="And",
        num_params=2,
        num_indices=0,
        num_minors=1,
        type=EPi("A", Sort.PROP.sort, EPi("B", Sort.PROP.sort,
            EPi("motive", EPi("_", EApp(EApp(EConst("And", ()), EVar("A")), EVar("B")),
                ESort(UnivLevelParam("u"))),
                EPi("minor", EPi("hA", EVar("A"),
                    EPi("hB", EVar("B"), EApp(EVar("motive"), EApp(EApp(EApp(EApp(
                        EConst("And.intro", ()),
                        EVar("A")), EVar("B")), EVar("hA")), EVar("hB"))))),
                    EPi("t", EApp(EApp(EConst("And", ()), EVar("A")), EVar("B")),
                        EApp(EVar("motive"), EVar("t"))
                    )
                )
            )
        ))
    )

    """Or (∨) inductive declaration for logical disjunction."""
    OR_DECLARATION = InductiveDeclaration(
        name="Or",
        level_params=(),
        type=EPi("A", Sort.PROP.sort, EPi("B", Sort.PROP.sort, Sort.PROP.sort)),
        constructor_names=("Or.inl", "Or.inr"),
    )

    """Or.inl constructor declaration for logical disjunction."""
    OR_INL_DECLARATION = ConstructorDeclaration(
        name="Or.inl",
        level_params=(),
        inductive_name="Or",
        type=EPi("A", Sort.PROP.sort, EPi("B", Sort.PROP.sort,
            EPi("hA", EVar("A"),
                EApp(EApp(EConst("Or", ()), EVar("A")), EVar("B")),
            ),
        ),),
    )

    """Or.inr constructor declaration for logical disjunction."""
    OR_INR_DECLARATION = ConstructorDeclaration(
        name="Or.inr",
        level_params=(),
        inductive_name="Or",
        type=EPi("A", Sort.PROP.sort, EPi("B", Sort.PROP.sort,
            EPi("hB", EVar("B"),
                EApp(EApp(EConst("Or", ()), EVar("A")), EVar("B")),
            ),
        ),),
    )

    """Or.rec recursor declaration (Disjunction Elimination / Proof by Cases)."""
    OR_REC_DECLARATION = RecursorDeclaration(
        name="Or.rec",
        level_params=("u",),
        inductive_name="Or",
        num_params=2,
        num_indices=0,
        num_minors=2,
        type=EPi("A", Sort.PROP.sort, EPi("B", Sort.PROP.sort,
            EPi("motive", EPi("_", EApp(EApp(EConst("Or", ()), EVar("A")), EVar("B")),
                ESort(UnivLevelParam("u"))),
                EPi("minor_inl", EPi("hA", EVar("A"), EApp(EVar("motive"),
                    EApp(EApp(EApp(
                        EConst("Or.inl", ()), EVar("A")), EVar("B")), EVar("hA")))),
                    EPi("minor_inr", EPi("hB", EVar("B"), EApp(EVar("motive"),
                        EApp(EApp(EApp(
                            EConst("Or.inr", ()), EVar("A")), EVar("B")), EVar("hB")))),
                        EPi("t", EApp(EApp(EConst("Or", ()), EVar("A")), EVar("B")),
                            EApp(EVar("motive"), EVar("t"))
                        )
                    )
                )
            )
        ))
    )

    """Not (¬) definition declaration for logical negation."""
    NOT_DECLARATION = DefinitionDeclaration(
        name="Not",
        level_params=(),
        type=EPi("A", Sort.PROP.sort, Sort.PROP.sort),
        value=ELam("A", Sort.PROP.sort, EPi("_", EVar("A"), EConst("False", ()))),
    )

    """Exists (∃) inductive declaration for existential quantification."""
    EXISTS_DECLARATION = InductiveDeclaration(
        name="Exists",
        level_params=("u",),
        type=EPi(
            "A",
            ESort(UnivLevelParam("u")),
            EPi(
                "p",
                EPi("_", EVar("A"), Sort.PROP.sort),
                Sort.PROP.sort,
            ),
        ),
        constructor_names=("Exists.intro",),
    )

    """Exists.intro constructor declaration."""
    EXISTS_INTRO_DECLARATION = ConstructorDeclaration(
        name="Exists.intro",
        level_params=("u",),
        inductive_name="Exists",
        type=EPi(
            "A",
            ESort(UnivLevelParam("u")),
            EPi(
                "p",
                EPi("_", EVar("A"), Sort.PROP.sort),
                EPi(
                    "w",
                    EVar("A"),
                    EPi(
                        "h",
                        EApp(EVar("p"), EVar("w")),
                        EApp(
                            EApp(
                                EConst("Exists", (UnivLevelParam("u"),)),
                                EVar("A"),
                            ),
                            EVar("p"),
                        ),
                    ),
                ),
            ),
        ),
    )

    """Exists.rec recursor declaration for existential elimination."""
    EXISTS_REC_DECLARATION = RecursorDeclaration(
        name="Exists.rec",
        level_params=("u", "v"),
        inductive_name="Exists",
        num_params=2,
        num_indices=0,
        num_minors=1,
        type=EPi(
            "A",
            ESort(UnivLevelParam("u")),
            EPi(
                "p",
                EPi("_", EVar("A"), Sort.PROP.sort),
                EPi(
                    "motive",
                    EPi(
                        "_",
                        EApp(
                            EApp(
                                EConst("Exists", (UnivLevelParam("u"),)),
                                EVar("A"),
                            ),
                            EVar("p"),
                        ),
                        ESort(UnivLevelParam("v")),
                    ),
                    EPi(
                        "minor",
                        EPi(
                            "w",
                            EVar("A"),
                            EPi(
                                "h",
                                EApp(EVar("p"), EVar("w")),
                                EApp(
                                    EVar("motive"),
                                    EApp(
                                        EApp(
                                            EApp(
                                                EApp(
                                                    EConst(
                                                        "Exists.intro",
                                                        (UnivLevelParam("u"),),
                                                    ),
                                                    EVar("A"),
                                                ),
                                                EVar("p"),
                                            ),
                                            EVar("w"),
                                        ),
                                        EVar("h"),
                                    ),
                                ),
                            ),
                        ),
                        EPi(
                            "t",
                            EApp(
                                EApp(
                                    EConst("Exists", (UnivLevelParam("u"),)),
                                    EVar("A"),
                                ),
                                EVar("p"),
                            ),
                            EApp(EVar("motive"), EVar("t")),
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
