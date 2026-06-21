"""
Public tactic API.
"""
from .apply import apply
from .constructor import constructor, left, right
from .exact import exact, assumption
from .intro import intro, intros
from .logic import exfalso, trivial

__all__ = [
    "apply",
    "constructor",
    "left",
    "right",
    "exact",
    "assumption",
    "intro",
    "intros",
    "exfalso",
    "trivial",
]
