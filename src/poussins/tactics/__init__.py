"""
Public tactic API.
"""
from .apply import apply
from .constructor import constructor
from .exact import exact, assumption
from .intro import intro, intros
from .logic import exfalso


__all__ = [
    "apply",
    "constructor",
    "exact",
    "assumption",
    "intro",
    "intros",
    "exfalso"
]
