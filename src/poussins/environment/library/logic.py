from __future__ import annotations
from enum import Enum

from .sort import Sort
from ..declaration import ConstantDeclaration, ConstructorDeclaration, Declaration, InductiveDeclaration
from ...ast.expr import EConst, EPi, EVar, ELam, EApp


class LogicDeclaration(Enum):
    """
    Standard logical declarations for propositions and connectives.
    """

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

    """False (⊥) inductive declaration for logical falsehood."""
    FALSE_DECLARATION = InductiveDeclaration(
        name="False",
        level_params=(),
        type=Sort.PROP.sort,
        constructor_names=(),
    )
    """False.elim constant declaration for logical falsehood."""
    FALSE_ELIM_DECLARATION = ConstantDeclaration(
        name="False.elim",
        level_params=(),
        type=EPi("P", Sort.PROP.sort, EPi("_", EConst("False", ()), EVar("P"))),
        value=None,
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
        type=EPi(
            "A",
            Sort.PROP.sort,
            EPi(
                "B",
                Sort.PROP.sort,
                EPi(
                    "hA",
                    EVar("A"),
                    EPi(
                        "hB",
                        EVar("B"),
                        EApp(EApp(EConst("And", ()), EVar("A")), EVar("B")),
                    ),
                ),
            ),
        ),
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
        type=EPi(
            "A",
            Sort.PROP.sort,
            EPi(
                "B",
                Sort.PROP.sort,
                EPi(
                    "hA",
                    EVar("A"),
                    EApp(EApp(EConst("Or", ()), EVar("A")), EVar("B")),
                ),
            ),
        ),
    )
    """Or.inr constructor declaration for logical disjunction."""
    OR_INR_DECLARATION = ConstructorDeclaration(
        name="Or.inr",
        level_params=(),
        inductive_name="Or",
        type=EPi(
            "A",
            Sort.PROP.sort,
            EPi(
                "B",
                Sort.PROP.sort,
                EPi(
                    "hB",
                    EVar("B"),
                    EApp(EApp(EConst("Or", ()), EVar("A")), EVar("B")),
                ),
            ),
        ),
    )

    """Not (¬) constant declaration for logical negation."""
    NOT_DECLARATION = ConstantDeclaration(
        name="Not",
        level_params=(),
        type=EPi("A", Sort.PROP.sort, Sort.PROP.sort),
        value=ELam("A", Sort.PROP.sort, EPi("_", EVar("A"), EConst("False", ()))),
    )


    @property
    def declaration(self) -> Declaration:
        """Return the underlying declaration."""
        return self.value
