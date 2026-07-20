"""
Public tactic API.
"""
from .apply import apply
from .exact import exact
from .intro import intro

__all__ = [
    "apply",
    "exact",
    "intro",
]
