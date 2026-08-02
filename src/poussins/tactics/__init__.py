"""
Public tactic API.
"""
from .apply import apply
from .cases import cases
from .change import change
from .constructor import constructor, left, right, split
from .exact import exact, assumption
from .intro import intro, intros
from .logic import exfalso
from .induction import induction


__all__ = [
    "apply",
    "cases",
    "change",
    "constructor",
    "left",
    "right",
    "split",
    "exact",
    "assumption",
    "intro",
    "intros",
    "exfalso",
    "induction"
]
