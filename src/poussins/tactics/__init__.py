"""
Public tactic API.
"""
from .primitive import intro, exact, apply, constructor
from .derived import intros, assumption

__all__ = [
    # Primitive tactics
    "intro",
    "exact",
    "apply",
    "constructor",
    # Derived tactics
    "intros",
    "assumption",
]
