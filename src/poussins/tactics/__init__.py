"""Public tactic API."""


from .primitive import intro, exact, apply
from .derived import intros


__all__ = [
    "intro",
    "exact",
    "apply",
    "intros"
]
