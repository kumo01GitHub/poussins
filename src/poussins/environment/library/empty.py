"""Empty declarations."""
from __future__ import annotations

from ...ast import Sort
from ..spec import InductiveSpec

EMPTY_IND_SPEC = InductiveSpec(
    name="Empty",
    type=Sort.TYPE.sort,
    constructors=(),
)
