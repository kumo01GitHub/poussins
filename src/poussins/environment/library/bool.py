"""Boolean declarations."""
from __future__ import annotations

from ...ast import EConst, Sort
from ..spec import InductiveSpec

BOOL_IND_SPEC = InductiveSpec(
    name="Bool",
    type=Sort.TYPE.sort,
    constructors=(
        ("Bool.true", EConst("Bool", ())),
        ("Bool.false", EConst("Bool", ())),
    ),
)
