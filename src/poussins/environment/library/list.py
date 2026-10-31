"""List declarations."""
from __future__ import annotations

from ...ast import EConst, EPi, app, pi, sort, univ_levels
from ..spec import InductiveSpec

LIST_IND_SPEC = InductiveSpec(
    name="List",
    type=EPi("A", sort("u"), sort("u")),
    constructors=(
        (
            "List.nil",
            EPi("A", sort("u"), app(EConst("List", univ_levels(("u",))), "A"))
        ),
        (
            "List.cons",
            pi(
                (
                    ("A", sort("u")),
                    ("head", "A"),
                    ("tail", app(EConst("List", univ_levels(("u",))), "A")),
                ),
                app(EConst("List", univ_levels(("u",))), "A")
            )
        )
    ),
)
