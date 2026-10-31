"""Length-indexed vector declarations."""
from __future__ import annotations

from ...ast import EConst, app, pi, sort, univ_levels
from ..spec import InductiveSpec

VECTOR_IND_SPEC = InductiveSpec(
    name="Vector",
    type=pi(
        (
            ("A", sort("u")),
            ("n", EConst("Nat", ())),
        ),
        sort("u")
    ),
    constructors=(
        (
            "Vector.nil",
            pi(
                (
                    ("A", sort("u")),
                ),
                app(
                    EConst("Vector", univ_levels(("u",))),
                    "A",
                    EConst("Nat.zero", ()),
                ),
            )
        ),
        (
            "Vector.cons",
            pi(
                (
                    ("A", sort("u")),
                    ("n", EConst("Nat", ())),
                    ("head", "A"),
                    (
                        "tail",
                        app(
                            EConst("Vector", univ_levels(("u",))),
                            "A",
                            "n",
                        ),
                    ),
                ),
                app(
                    EConst("Vector", univ_levels(("u",))),
                    "A",
                    app(EConst("Nat.succ", ()), "n"),
                ),
            )
        ),
    ),
)
