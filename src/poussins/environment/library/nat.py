"""Natural numbers declarations."""
from __future__ import annotations

from ...ast import (
    EConst,
    EMatch,
    Sort,
    app,
    lam,
    pi,
)
from ..spec import DefinitionSpec, InductiveSpec

NAT_IND_SPEC = InductiveSpec(
    name="Nat",
    type=Sort.TYPE.sort,
    constructors=(
        ("Nat.zero", EConst("Nat", ())),
        ("Nat.succ", pi((("n", EConst("Nat", ())),), EConst("Nat", ()))),
    ),
)

NAT_ADD_DEF_SPEC = DefinitionSpec(
    name="Nat.add",
    type=pi(
        (
            ("n", EConst("Nat", ())),
            ("m", EConst("Nat", ())),
        ),
        EConst("Nat", ()),
    ),
    value=lam(
        (
            ("n", EConst("Nat", ())),
            ("m", EConst("Nat", ())),
        ),
        app(
            EConst("Nat.rec", (Sort.TYPE.level,)),
            lam(
                (("_", EConst("Nat", ())),),
                EConst("Nat", ()),
            ),
            "m",
            lam(
                (
                    ("n", EConst("Nat", ())),
                    ("ih", EConst("Nat", ())),
                ),
                app(EConst("Nat.succ", ()), "ih"),
            ),
            "n",
        ),
    )
)

NAT_SUB_DEF_SPEC = DefinitionSpec(
    name="Nat.sub",
    type=pi(
        (
            ("n", EConst("Nat", ())),
            ("m", EConst("Nat", ())),
        ),
        EConst("Nat", ()),
    ),
    value=lam(
        (
            ("n", EConst("Nat", ())),
            ("m", EConst("Nat", ())),
        ),
        app(
            EConst("Nat.rec", (Sort.TYPE.level,)),
            lam(
                (("_", EConst("Nat", ())),),
                EConst("Nat", ()),
            ),
            "n",
            lam(
                (
                    ("m", EConst("Nat", ())),
                    ("ih", EConst("Nat", ())),
                ),
                app(
                    EConst("Nat.rec", (Sort.TYPE.level,)),
                    lam(
                        (("_", EConst("Nat", ())),),
                        EConst("Nat", ()),
                    ),
                    EConst("Nat.zero", ()),
                    lam(
                        (
                            ("k", EConst("Nat", ())),
                            ("_", EConst("Nat", ())),
                        ),
                        "k",
                    ),
                    "ih",
                ),
            ),
            "m",
        ),
    ),
)

NAT_MUL_DEF_SPEC = DefinitionSpec(
    name="Nat.mul",
    type=pi(
        (
            ("n", EConst("Nat", ())),
            ("m", EConst("Nat", ())),
        ),
        EConst("Nat", ()),
    ),
    value=lam(
        (
            ("n", EConst("Nat", ())),
            ("m", EConst("Nat", ())),
        ),
        app(
            EConst("Nat.rec", (Sort.TYPE.level,)),
            lam(
                (("_", EConst("Nat", ())),),
                EConst("Nat", ()),
            ),
            EConst("Nat.zero", ()),
            lam(
                (
                    ("n", EConst("Nat", ())),
                    ("ih", EConst("Nat", ())),
                ),
                app(EConst("Nat.add", ()), "ih", "m"),
            ),
            "n",
        ),
    ),
)

NAT_DIV_DEF_SPEC = DefinitionSpec(
    name="Nat.div",
    type=pi(
        (
            ("n", EConst("Nat", ())),
            ("m", EConst("Nat", ())),
        ),
        EConst("Nat", ()),
    ),
    value=lam(
        (
            ("n", EConst("Nat", ())),
            ("m", EConst("Nat", ())),
        ),
        app(
            EConst("Nat.rec", (Sort.TYPE.level,)),
            lam(
                (("_", EConst("Nat", ())),),
                EConst("Nat", ()),
            ),
            EConst("Nat.zero", ()),
            lam(
                (
                    ("n_ih", EConst("Nat", ())),
                    ("ih", EConst("Nat", ())),
                ),
                EMatch(
                    inductive_name="Nat",
                    discriminee=app(
                        EConst("Nat.sub", ()),
                        "m",
                        app(
                            EConst("Nat.succ", ()),
                            app(
                                EConst("Nat.rec", (Sort.TYPE.level,)),
                                lam(
                                    (("_", EConst("Nat", ())),),
                                    EConst("Nat", ()),
                                ),
                                EConst("Nat.zero", ()),
                                lam(
                                    (
                                        ("n_ih2", EConst("Nat", ())),
                                        ("ih2", EConst("Nat", ())),
                                    ),
                                    EMatch(
                                        inductive_name="Nat",
                                        discriminee=app(
                                            EConst("Nat.sub", ()),
                                            "m",
                                            app(EConst("Nat.succ", ()), "ih2"),
                                        ),
                                        motive=lam(
                                            (("_", EConst("Nat", ())),),
                                            EConst("Nat", ()),
                                        ),
                                        cases=(
                                            EConst("Nat.zero", ()),
                                            lam(
                                                (
                                                    ("k", EConst("Nat", ())),
                                                ),
                                                app(EConst("Nat.succ", ()), "ih2"),
                                            ),
                                        ),
                                    ),
                                ),
                                "n_ih",
                            ),
                        ),
                    ),
                    motive=lam(
                        (("_", EConst("Nat", ())),),
                        EConst("Nat", ()),
                    ),
                    cases=(
                        EConst("Nat.zero", ()),
                        lam(
                            (
                                ("k", EConst("Nat", ())),
                            ),
                            app(EConst("Nat.succ", ()), "ih"),
                        ),
                    ),
                ),
            ),
            "n",
        ),
    ),
)

NAT_MOD_DEF_SPEC = DefinitionSpec(
    name="Nat.mod",
    type=pi(
        (
            ("n", EConst("Nat", ())),
            ("m", EConst("Nat", ())),
        ),
        EConst("Nat", ()),
    ),
    value=lam(
        (
            ("n", EConst("Nat", ())),
            ("m", EConst("Nat", ())),
        ),
        app(
            EConst("Nat.rec", (Sort.TYPE.level,)),
            lam(
                (("_", EConst("Nat", ())),),
                EConst("Nat", ()),
            ),
            EConst("Nat.zero", ()),
            lam(
                (
                    ("n_ih", EConst("Nat", ())),
                    ("ih", EConst("Nat", ())),
                ),
                EMatch(
                    inductive_name="Nat",
                    discriminee=app(
                        EConst("Nat.sub", ()),
                        "m",
                        app(EConst("Nat.succ", ()), "ih"),
                    ),
                    motive=lam(
                        (("_", EConst("Nat", ())),),
                        EConst("Nat", ()),
                    ),
                    cases=(
                        EConst("Nat.zero", ()),
                        lam(
                            (("k", EConst("Nat", ())),),
                            app(EConst("Nat.succ", ()), "ih"),
                        ),
                    ),
                ),
            ),
            "n",
        ),
    ),
)
