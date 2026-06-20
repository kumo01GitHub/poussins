"""
Public tactic API.
"""
from .primitive import intro, exact, apply
from .derived import intros, assumption

__all__ = [
    # Primitive tactics
    "intro",
    "exact",
    "apply",
    # Derived tactics
    "intros",
    "assumption",
]
