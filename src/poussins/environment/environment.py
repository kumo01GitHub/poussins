"""
Environment storage and predefined logical declarations.
"""
from __future__ import annotations
from typing import Final

from .declaration import (
    Declaration,
    ConstantDeclaration,
    ConstructorDeclaration,
    InductiveDeclaration,
)
from ..ast import (
    ESort, EConst, EVar, EPi, EApp, ELam,
    UnivLevelZero, UnivLevelSucc
)


class Environment:
    """
    Collection of named declarations used by the proof engine.
    """

    """Proposition sort (⊥) for logical propositions."""
    PROP_SORT: Final[ESort] = ESort(UnivLevelZero())
    """Type sort (⊤) for types and data structures."""
    TYPE_SORT: Final[ESort] = ESort(UnivLevelSucc(UnivLevelZero()))

    """True (⊤) inductive declaration for logical truth."""
    TRUE_DECLARATION: Final[InductiveDeclaration] = InductiveDeclaration(
        name="True",
        level_params=(),
        type=PROP_SORT,
        constructor_names=("True.intro",),
    )
    """True.intro constructor declaration for logical truth."""
    TRUE_INTRO_DECLARATION: Final[ConstructorDeclaration] = ConstructorDeclaration(
        name="True.intro",
        level_params=(),
        inductive_name="True",
        type=EConst("True", ()),
    )

    """False (⊥) inductive declaration for logical falsehood."""
    FALSE_DECLARATION: Final[InductiveDeclaration] = InductiveDeclaration(
        name="False",
        level_params=(),
        type=PROP_SORT,
        constructor_names=(),
    )
    """False.elim constant declaration for logical falsehood."""
    FALSE_ELIM_DECLARATION: Final[ConstantDeclaration] = ConstantDeclaration(
        name="False.elim",
        level_params=(),
        type=EPi("P", PROP_SORT, EPi("_", EConst("False", ()), EVar("P"))),
        value=None,
    )

    """And (∧) inductive declaration for logical conjunction."""
    AND_DECLARATION: Final[InductiveDeclaration] = InductiveDeclaration(
        name="And",
        level_params=(),
        type=EPi("A", PROP_SORT, EPi("B", PROP_SORT, PROP_SORT)),
        constructor_names=("And.intro",),
    )
    """And.intro constructor declaration for logical conjunction."""
    AND_INTRO_DECLARATION: Final[ConstructorDeclaration] = ConstructorDeclaration(
        name="And.intro",
        level_params=(),
        inductive_name="And",
        type=EPi(
            "A",
            PROP_SORT,
            EPi(
                "B",
                PROP_SORT,
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
    OR_DECLARATION: Final[InductiveDeclaration] = InductiveDeclaration(
        name="Or",
        level_params=(),
        type=EPi("A", PROP_SORT, EPi("B", PROP_SORT, PROP_SORT)),
        constructor_names=("Or.inl", "Or.inr"),
    )
    """Or.inl constructor declaration for logical disjunction."""
    OR_INL_DECLARATION: Final[ConstructorDeclaration] = ConstructorDeclaration(
        name="Or.inl",
        level_params=(),
        inductive_name="Or",
        type=EPi(
            "A",
            PROP_SORT,
            EPi(
                "B",
                PROP_SORT,
                EPi(
                    "hA",
                    EVar("A"),
                    EApp(EApp(EConst("Or", ()), EVar("A")), EVar("B")),
                ),
            ),
        ),
    )
    """Or.inr constructor declaration for logical disjunction."""
    OR_INR_DECLARATION: Final[ConstructorDeclaration] = ConstructorDeclaration(
        name="Or.inr",
        level_params=(),
        inductive_name="Or",
        type=EPi(
            "A",
            PROP_SORT,
            EPi(
                "B",
                PROP_SORT,
                EPi(
                    "hB",
                    EVar("B"),
                    EApp(EApp(EConst("Or", ()), EVar("A")), EVar("B")),
                ),
            ),
        ),
    )

    """Not (¬) constant declaration for logical negation."""
    NOT_DECLARATION: Final[ConstantDeclaration] = ConstantDeclaration(
        name="Not",
        level_params=(),
        type=EPi("A", PROP_SORT, PROP_SORT),
        value=ELam("A", PROP_SORT, EPi("_", EVar("A"), EConst("False", ()))),
    )

    """Eq inductive declaration for propositional equality."""
    EQ_DECLARATION: Final[InductiveDeclaration] = InductiveDeclaration(
        name="Eq",
        level_params=(),
        type=EPi("A", TYPE_SORT, EPi("x", EVar("A"), EPi("y", EVar("A"), PROP_SORT))),
        constructor_names=("Eq.refl",),
    )
    """Eq.refl constructor declaration for propositional equality."""
    EQ_REFL_DECLARATION: Final[ConstructorDeclaration] = ConstructorDeclaration(
        name="Eq.refl",
        level_params=(),
        inductive_name="Eq",
        type=EPi(
            "A",
            TYPE_SORT,
            EPi(
                "x",
                EVar("A"),
                EApp(EApp(EApp(EConst("Eq", ()), EVar("A")), EVar("x")), EVar("x")),
            ),
        ),
    )

    """Nat inductive declaration for natural numbers."""
    NAT_DECLARATION: Final[InductiveDeclaration] = InductiveDeclaration(
        name="Nat",
        level_params=(),
        type=TYPE_SORT,
        constructor_names=("Nat.zero", "Nat.succ"),
    )
    """Nat.zero constructor declaration for natural numbers."""
    NAT_ZERO_DECLARATION: Final[ConstructorDeclaration] = ConstructorDeclaration(
        name="Nat.zero",
        level_params=(),
        inductive_name="Nat",
        type=EConst("Nat", ()),
    )
    """Nat.succ constructor declaration for natural numbers."""
    NAT_SUCC_DECLARATION: Final[ConstructorDeclaration] = ConstructorDeclaration(
        name="Nat.succ",
        level_params=(),
        inductive_name="Nat",
        type=EPi("n", EConst("Nat", ()), EConst("Nat", ())),
    )

    def __init__(self):
        self.declarations: dict[str, Declaration] = {}

    def add(self, declaration: Declaration):
        """
        Add a declaration to the environment.
        """
        if declaration.name in self.declarations:
            raise ValueError(f"Declaration with name '{declaration.name}' already exists.")
        self.declarations[declaration.name] = declaration

    def get(self, name: str) -> Declaration | None:
        """
        Return the declaration with the given name, if it exists.
        """
        return self.declarations.get(name)

    def update(self, other: Environment):
        """
        Merge declarations from another environment into this one.
        """
        self.declarations.update(other.declarations)

    def items(self):
        """
        Return the environment declarations as `(name, declaration)` pairs.
        """
        return self.declarations.items()

    @classmethod
    def default(cls) -> Environment:
        """
        Create a default environment with the core logical declarations.
        """
        env = cls()

        # ------------------------------------------------------------------
        # True (Top)
        # ------------------------------------------------------------------
        env.add(cls.TRUE_DECLARATION)
        env.add(cls.TRUE_INTRO_DECLARATION)

        # ------------------------------------------------------------------
        # False (Bottom)
        # ------------------------------------------------------------------
        env.add(cls.FALSE_DECLARATION)
        env.add(cls.FALSE_ELIM_DECLARATION)

        # ------------------------------------------------------------------
        # And (Conjunction)
        # ------------------------------------------------------------------
        env.add(cls.AND_DECLARATION)
        env.add(cls.AND_INTRO_DECLARATION)

        # ------------------------------------------------------------------
        # Or (Disjunction)
        # ------------------------------------------------------------------
        env.add(cls.OR_DECLARATION)
        env.add(cls.OR_INL_DECLARATION)
        env.add(cls.OR_INR_DECLARATION)

        # ------------------------------------------------------------------
        # Not (Negation)
        # ------------------------------------------------------------------
        env.add(cls.NOT_DECLARATION)

        # ------------------------------------------------------------------
        # Eq (Propositional Equality)
        # ------------------------------------------------------------------
        env.add(cls.EQ_DECLARATION)
        env.add(cls.EQ_REFL_DECLARATION)

        # ------------------------------------------------------------------
        # Nat (Natural Numbers)
        # ------------------------------------------------------------------
        env.add(cls.NAT_DECLARATION)
        env.add(cls.NAT_ZERO_DECLARATION)
        env.add(cls.NAT_SUCC_DECLARATION)

        return env
