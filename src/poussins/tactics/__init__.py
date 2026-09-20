"""Public tactic API."""
from .apply import apply
from .cases import cases
from .change import change
from .constructor import constructor, left, right, split
from .exact import assumption, exact
from .have import have
from .induction import induction
from .intro import intro, intros
from .logic import contradiction, exfalso
from .refine import refine
from .reflexivity import reflexivity, rfl
from .revert import revert
from .rewrite import rewrite, rw
from .specialize import specialize
from .suffices import suffices

__all__ = [
    "apply",
    "assumption",
    "cases",
    "change",
    "constructor",
    "contradiction",
    "exact",
    "exfalso",
    "have",
    "induction",
    "intro",
    "intros",
    "left",
    "refine",
    "reflexivity",
    "revert",
    "rewrite",
    "rfl",
    "right",
    "rw",
    "specialize",
    "split",
    "suffices",
]
