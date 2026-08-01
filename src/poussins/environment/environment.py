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

    PROP_SORT: Final[ESort] = ESort(UnivLevelZero())
    TYPE_SORT: Final[ESort] = ESort(UnivLevelSucc(UnivLevelZero()))

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
        env.add(
            InductiveDeclaration(
                name="True",
                level_params=(),
                type=cls.PROP_SORT,
                constructor_names=("True.intro",),
            )
        )
        env.add(
            ConstructorDeclaration(
                name="True.intro",
                level_params=(),
                inductive_name="True",
                type=EConst("True", ()),
            )
        )

        # ------------------------------------------------------------------
        # False (Bottom)
        # ------------------------------------------------------------------
        env.add(
            InductiveDeclaration(
                name="False",
                level_params=(),
                type=cls.PROP_SORT,
                constructor_names=(),
            )
        )
        env.add(
            ConstantDeclaration(
                name="False.elim",
                level_params=(),
                type=EPi("P", cls.PROP_SORT, EPi("_", EConst("False", ()), EVar("P"))),
                value=None,
            )
        )

        # ------------------------------------------------------------------
        # And (Conjunction)
        # ------------------------------------------------------------------
        env.add(
            InductiveDeclaration(
                name="And",
                level_params=(),
                type=EPi("A", cls.PROP_SORT, EPi("B", cls.PROP_SORT, cls.PROP_SORT)),
                constructor_names=("And.intro",),
            )
        )
        env.add(
            ConstructorDeclaration(
                name="And.intro",
                level_params=(),
                inductive_name="And",
                type=EPi(
                    "A",
                    cls.PROP_SORT,
                    EPi(
                        "B",
                        cls.PROP_SORT,
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
        )

        # ------------------------------------------------------------------
        # Or (Disjunction)
        # ------------------------------------------------------------------
        env.add(
            InductiveDeclaration(
                name="Or",
                level_params=(),
                type=EPi("A", cls.PROP_SORT, EPi("B", cls.PROP_SORT, cls.PROP_SORT)),
                constructor_names=("Or.inl", "Or.inr"),
            )
        )
        env.add(
            ConstructorDeclaration(
                name="Or.inl",
                level_params=(),
                inductive_name="Or",
                type=EPi(
                    "A",
                    cls.PROP_SORT,
                    EPi(
                        "B",
                        cls.PROP_SORT,
                        EPi(
                            "hA",
                            EVar("A"),
                            EApp(EApp(EConst("Or", ()), EVar("A")), EVar("B")),
                        ),
                    ),
                ),
            )
        )
        env.add(
            ConstructorDeclaration(
                name="Or.inr",
                level_params=(),
                inductive_name="Or",
                type=EPi(
                    "A",
                    cls.PROP_SORT,
                    EPi(
                        "B",
                        cls.PROP_SORT,
                        EPi(
                            "hB",
                            EVar("B"),
                            EApp(EApp(EConst("Or", ()), EVar("A")), EVar("B")),
                        ),
                    ),
                ),
            )
        )

        # Not (negation).
        env.add(
            ConstantDeclaration(
                name="Not",
                level_params=(),
                type=EPi("A", cls.PROP_SORT, cls.PROP_SORT),
                value=ELam("A", cls.PROP_SORT, EPi("_", EVar("A"), EConst("False", ()))),
            )
        )

        # ------------------------------------------------------------------
        # Nat (Natural Numbers)
        # ------------------------------------------------------------------
        env.add(
            InductiveDeclaration(
                name="Nat",
                level_params=(),
                type=cls.TYPE_SORT,
                constructor_names=("Nat.zero", "Nat.succ"),
            )
        )
        # Nat.zero
        env.add(
            ConstructorDeclaration(
                name="Nat.zero",
                level_params=(),
                inductive_name="Nat",
                type=EConst("Nat", ()),
            )
        )
        # Nat.succ
        env.add(
            ConstructorDeclaration(
                name="Nat.succ",
                level_params=(),
                inductive_name="Nat",
                type=EPi("n", EConst("Nat", ()), EConst("Nat", ())),
            )
        )

        return env
