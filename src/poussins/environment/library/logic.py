""""Standard logical declarations."""
from __future__ import annotations

from ...ast import EConst, Sort, app, lam, pi, sort, univ_levels
from ..spec import DefinitionSpec, InductiveSpec

TRUE_IND_SPEC = InductiveSpec(
    name="True",
    type=Sort.PROP.sort,
    constructors=(
        ("True.intro", EConst("True", ())),
    ),
)

FALSE_IND_SPEC = InductiveSpec(
    name="False",
    type=Sort.PROP.sort,
    constructors=(),
)

AND_IND_SPEC = InductiveSpec(
    name="And",
    type=pi(
        (
            ("A", Sort.PROP.sort),
            ("B", Sort.PROP.sort),
        ),
        Sort.PROP.sort,
    ),
    constructors=(
        (
            "And.intro",
            pi(
                (
                    ("A", Sort.PROP.sort),
                    ("B", Sort.PROP.sort),
                    ("hA", "A"),
                    ("hB", "B"),
                ),
                app(EConst("And", ()), "A", "B")
            ),
        ),
    ),
)

OR_IND_SPEC = InductiveSpec(
    name="Or",
    type=pi(
        (
            ("A", Sort.PROP.sort),
            ("B", Sort.PROP.sort),
        ),
        Sort.PROP.sort,
    ),
    constructors=(
        (
            "Or.inl",
            pi(
                (
                    ("A", Sort.PROP.sort),
                    ("B", Sort.PROP.sort),
                    ("hA", "A"),
                ),
                app(EConst("Or", ()), "A", "B")
            ),
        ),
        (
            "Or.inr",
            pi(
                (
                    ("A", Sort.PROP.sort),
                    ("B", Sort.PROP.sort),
                    ("hB", "B"),
                ),
                app(EConst("Or", ()), "A", "B")
            ),
        ),
    ),
)

NOT_DEF_SPEC = DefinitionSpec(
    name="Not",
    type=pi(
        (
            ("A", Sort.PROP.sort),
        ),
        Sort.PROP.sort,
    ),
    value=lam(
        (("A", Sort.PROP.sort),),
        pi((("_", "A"),), EConst("False", ()))
    )
)

EXISTS_IND_SPEC = InductiveSpec(
    name="Exists",
    type=pi(
        (
            ("A", sort("u")),
            ("p", pi((("_", "A"),), Sort.PROP.sort)),
        ),
        Sort.PROP.sort,
    ),
    constructors=(
        (
          "Exists.intro",
          pi(
              (
                ("A", sort("u")),
                ("p", pi((("_", "A"),), Sort.PROP.sort)),
                ("w", "A"),
                ("h", app("p", "w")),
              ),
              app(EConst("Exists", univ_levels(("u",))), "A", "p")
          ),
        ),
    ),
)
