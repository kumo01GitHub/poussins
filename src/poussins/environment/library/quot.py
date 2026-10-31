"""Quotient-type declarations."""
from __future__ import annotations

from ...ast import EConst, Sort, app, pi, sort, univ_levels
from ..declaration import AxiomDeclaration, QuotientDeclaration

QUOT_DECLARATION = QuotientDeclaration(
    name="Quot",
    level_params=("u",),
    type=pi(
        (
            ("A", sort("u")),
            ("r", pi((("x", "A"), ("y", "A")), Sort.PROP.sort)),
        ),
        sort("u")
    ),
    kind="type",
)

QUOT_MK_DECLARATION = QuotientDeclaration(
    name="Quot.mk",
    level_params=("u",),
    type=pi(
        (
            ("A", sort("u")),
            ("r", pi((("x", "A"), ("y", "A")), Sort.PROP.sort)),
            ("a", "A"),
        ),
        app(EConst("Quot", univ_levels(("u",))), "A", "r"),
    ),
    kind="mk",
)

QUOT_LIFT_DECLARATION = QuotientDeclaration(
    name="Quot.lift",
    level_params=("u", "v"),
    type=pi(
        (
            ("A", sort("u")),
            ("r", pi((("x", "A"), ("y", "A")), Sort.PROP.sort)),
            ("B", sort("v")),
            ("f", pi((("x", "A"),), "B")),
            (
                "h",
                pi(
                    (
                        ("x", "A"),
                        ("y", "A"),
                        ("hr", app("r", "x", "y")),
                    ),
                    app(
                        EConst("Eq", univ_levels(("v",))),
                        "B",
                        app("f", "x"),
                        app("f", "y"),
                    ),
                ),
            ),
        ),
        pi(
            (("q", app(EConst("Quot", univ_levels(("u",))), "A", "r")),),
            "B",
        ),
    ),
    kind="lift",
)

QUOT_IND_DECLARATION = QuotientDeclaration(
    name="Quot.ind",
    level_params=("u",),
    type=pi(
        (
            ("A", sort("u")),
            ("r", pi((("x", "A"), ("y", "A")), Sort.PROP.sort)),
            (
                "motive",
                pi(
                    (
                        (
                            "q",
                            app(
                                EConst("Quot", univ_levels(("u",))),
                                "A",
                                "r",
                            ),
                        ),
                    ),
                    Sort.PROP.sort,
                ),
            ),
            (
                "h",
                pi(
                    (("a", "A"),),
                    app(
                        "motive",
                        app(
                            EConst("Quot.mk", univ_levels(("u",))),
                            "A",
                            "r",
                            "a",
                        ),
                    ),
                ),
            ),
        ),
        pi(
            (
                (
                    "q",
                    app(EConst("Quot", univ_levels(("u",))), "A", "r"),
                ),
            ),
            app("motive", "q"),
        ),
    ),
    kind="ind",
)

QUOT_SOUND_DECLARATION = AxiomDeclaration(
    name="Quot.sound",
    level_params=("u",),
    type=pi(
        (
            ("A", sort("u")),
            ("r", pi((("x", "A"), ("y", "A")), Sort.PROP.sort)),
            ("a", "A"),
            ("b", "A"),
            ("h", app("r", "a", "b")),
        ),
        app(
            EConst("Eq", univ_levels(("u",))),
            app(EConst("Quot", univ_levels(("u",))), "A", "r"),
            app(EConst("Quot.mk", univ_levels(("u",))), "A", "r", "a"),
            app(EConst("Quot.mk", univ_levels(("u",))), "A", "r", "b"),
        ),
    ),
)
