"""Sum-type declarations."""
from __future__ import annotations

from ...ast import EConst, app, pi, sort, univ_levels
from ..spec import InductiveSpec

SUM_IND_SPEC = InductiveSpec(
    name="Sum",
    type=pi(
        (
            ("A", sort("u")),
            ("B", sort("u")),
        ),
        sort("u"),
    ),
    constructors=(
        (
            "Sum.inl",
            pi(
                (
                    ("A", sort("u")),
                    ("B", sort("u")),
                    ("value", "A"),
                ),
                app(EConst("Sum", univ_levels(("u",))), "A", "B"),
            )
        ),
        (
            "Sum.inr",
            pi(
                (
                    ("A", sort("u")),
                    ("B", sort("u")),
                    ("value", "B"),
                ),
                app(EConst("Sum", univ_levels(("u",))), "A", "B"),
            )
        ),
    )
)
