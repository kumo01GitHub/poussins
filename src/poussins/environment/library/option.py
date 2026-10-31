"""Optional-value declarations."""
from __future__ import annotations

from ...ast import EConst, app, pi, sort, univ_levels
from ..spec import InductiveSpec

OPTION_IND_SPEC = InductiveSpec(
    name="Option",
    type=pi(
        (("A", sort("u")),),
        sort("u"),
    ),
    constructors=(
        (
            "Option.none",
            pi(
                (("A", sort("u")),),
                app(EConst("Option", univ_levels("u")), "A"),
            ),
        ),
        (
            "Option.some",
            pi(
                (
                    ("A", sort("u")),
                    ("value", "A"),
                ),
                app(EConst("Option", univ_levels("u")), "A"),
            ),
        ),
    ),
)
