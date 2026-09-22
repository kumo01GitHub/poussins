"""Public tactic API."""
from .apply import apply
from .cases import RCasesPattern, cases, obtain, rcases
from .change import change
from .constructor import constructor, left, right, split
from .equality import reflexivity, rfl, symm, symmetry, trans, transitivity
from .exact import assumption, exact
from .exists import exists, use
from .have import have
from .induction import induction
from .intro import intro, intros
from .logic import contradiction, exfalso
from .refine import refine
from .revert import revert
from .rewrite import rewrite, rw
from .simpl import dsimp, simpl, unfold
from .specialize import specialize
from .suffices import suffices

__all__ = [
    "RCasesPattern",
    "apply",
    "assumption",
    "cases",
    "change",
    "constructor",
    "contradiction",
    "dsimp",
    "exact",
    "exfalso",
    "exists",
    "have",
    "induction",
    "intro",
    "intros",
    "left",
    "obtain",
    "rcases",
    "refine",
    "reflexivity",
    "revert",
    "rewrite",
    "rfl",
    "right",
    "rw",
    "simpl",
    "specialize",
    "split",
    "suffices",
    "symm",
    "symmetry",
    "trans",
    "transitivity",
    "unfold",
    "use",
]
