"""Direct-product declarations."""
from __future__ import annotations

from ...ast import EConst, UnivLevelMax, UnivLevelParam, app, pi, sort, univ_levels
from ..spec import InductiveSpec

PROD_IND_SPEC = InductiveSpec(
    name="Prod",
    type=pi(
        (
            ("A", sort("u")),
            ("B", sort("v")),
        ),
        sort(UnivLevelMax(UnivLevelParam("u"), UnivLevelParam("v"))),
    ),
    constructors=(
        (
            "Prod.mk",
            pi(
                (
                    ("A", sort("u")),
                    ("B", sort("v")),
                    ("fst", "A"),
                    ("snd", "B"),
                ),
                app(
                    EConst("Prod", univ_levels(("u", "v"))),
                    "A",
                    "B",
                ),
            ),
        ),
    ),
)
