"""Unit declarations."""
from __future__ import annotations

from ...ast import EConst, Sort
from ..spec import InductiveSpec

UNIT_IND_SPEC = InductiveSpec(
    name="Unit",
    type=Sort.TYPE.sort,
    constructors=(
        (
            "Unit.unit",
            EConst("Unit", ()),
        ),
    ),
)
