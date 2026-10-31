"""Equality declarations."""
from __future__ import annotations

from ...ast import (
    EConst,
    Sort,
    app,
    lam,
    pi,
    sort,
    univ_levels,
)
from ..spec import DefinitionSpec, InductiveSpec

EQ_IND_SPEC = InductiveSpec(
    name="Eq",
    type=pi(
        (
            ("A", sort("u")),
            ("x", "A"),
            ("y", "A"),
        ),
        Sort.PROP.sort
    ),
    constructors=(
        (
            "Eq.refl",
            pi(
                (
                    ("A", sort("u")),
                    ("x", "A"),
                ),
                app(EConst("Eq", univ_levels(("u",))), "A", "x", "x"),
            )
        ),
    ),
)

EQ_SYMM_DEF_SPEC = DefinitionSpec(
    name="Eq.symm",
    type=pi(
        (
            ("A", sort("u")),
            ("x", "A"),
            ("y", "A"),
            ("h", app(EConst("Eq", univ_levels(("u",))), "A", "x", "y")),
        ),
        app(EConst("Eq", univ_levels(("u",))), "A", "y", "x"),
    ),
    value=lam(
        (
            ("A", sort("u")),
            ("x", "A"),
            ("y", "A"),
            ("h", app(EConst("Eq", univ_levels(("u",))), "A", "x", "y")),
        ),
        app(
            EConst("Eq.rec", univ_levels(("u", Sort.PROP.level))),
            "A",
            "x",
            lam(
                (
                    ("z", "A"),
                    ("_", app(EConst("Eq", univ_levels(("u",))), "A", "x", "z")),
                ),
                app(EConst("Eq", univ_levels(("u",))), "A", "z", "x"),
            ),
            app(EConst("Eq.refl", univ_levels(("u",))), "A", "x"),
            "y",
            "h",
        ),
    ),
)

EQ_TRANS_DEF_SPEC = DefinitionSpec(
    name="Eq.trans",
    type=pi(
        (
            ("A", sort("u")),
            ("x", "A"),
            ("y", "A"),
            ("z", "A"),
            ("h1", app(EConst("Eq", univ_levels(("u",))), "A", "x", "y")),
            ("h2", app(EConst("Eq", univ_levels(("u",))), "A", "y", "z")),
        ),
        app(EConst("Eq", univ_levels(("u",))), "A", "x", "z"),
    ),
    value=lam(
        (
            ("A", sort("u")),
            ("x", "A"),
            ("y", "A"),
            ("z", "A"),
            ("h1", app(EConst("Eq", univ_levels(("u",))), "A", "x", "y")),
            ("h2", app(EConst("Eq", univ_levels(("u",))), "A", "y", "z")),
        ),
        app(
            EConst("Eq.rec", univ_levels(("u", Sort.PROP.level))),
            "A",
            "y",
            lam(
                (
                    ("z'", "A"),
                    ("_", app(EConst("Eq", univ_levels(("u",))), "A", "y", "z'")),
                ),
                app(EConst("Eq", univ_levels(("u",))), "A", "x", "z'"),
            ),
            "h1",
            "z",
            "h2",
        ),
    ),
)
