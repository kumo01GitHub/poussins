"""
Public tactic API.
"""
from .apply import apply
from .cases import cases
from .constructor import constructor
from .exact import exact, assumption
from .intro import intro, intros
from .logic import exfalso


__all__ = [
    "apply",
    "cases",
    "constructor",
    "exact",
    "assumption",
    "intro",
    "intros",
    "exfalso"
]
