"""Dependent-pair declarations."""
from __future__ import annotations

from ...ast import EConst, UnivLevelIMax, app, pi, sort, univ_level, univ_levels
from ..spec import InductiveSpec

SIGMA_IND_SPEC = InductiveSpec(
    name="Sigma",
    type=pi(
        (
            ("A", sort("u")),
            ("B", pi((("_", "A"),), sort("v"))),
        ),
        sort(UnivLevelIMax(univ_level("u"), univ_level("v"))),
    ),
    constructors=(
        (
            "Sigma.mk",
            pi(
                (
                    ("A", sort("u")),
                    ("B", pi((("_", "A"),), sort("v"))),
                    ("fst", "A"),
                    ("snd", app("B", "fst")),
                ),
                app(EConst("Sigma", univ_levels(("u", "v"))), "A", "B"),
            )
        ),
    )
)
