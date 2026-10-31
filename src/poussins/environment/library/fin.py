"""Finite-index declarations."""
from __future__ import annotations

from ...ast import EConst, EPi, Sort, app, pi
from ..spec import InductiveSpec

FIN_IND_SPEC = InductiveSpec(
    name="Fin",
    type=EPi("n", EConst("Nat", ()), Sort.TYPE.sort),
    constructors=(
        (
            "Fin.zero",
            pi(
                (("n", EConst("Nat", ())),),
                app(EConst("Fin", ()), app(EConst("Nat.succ", ()), "n"))
            )
        ),
        (
            "Fin.succ",
            pi(
                (
                    ("n", EConst("Nat", ())),
                    ("value", app(EConst("Fin", ()), "n")),
                ),
                app(EConst("Fin", ()), app(EConst("Nat.succ", ()), "n")),
            )
        ),
    ),
)
