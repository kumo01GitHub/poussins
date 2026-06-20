"""
Public tactic API.
"""
from .primitive import intro, exact, apply, split
from .derived import intros, assumption

__all__ = [
    # Primitive tactics
    "intro",
    "exact",
    "apply",
    "split",
    # Derived tactics
    "intros",
    "assumption",
]
