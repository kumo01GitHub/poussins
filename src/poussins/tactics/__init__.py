"""Public tactic API."""
from .apply import apply
from .cases import CasesPatterns, RCasesPattern, cases, rcases
from .change import change
from .clear import clear
from .constructor import constructor, left, right, split
from .equality import reflexivity, rfl, symm, symmetry, trans, transitivity
from .exact import assumption, exact
from .exists import exists, use
from .have import have
from .induction import induction
from .intro import intro, intros
from .logic import contradiction, exfalso
from .obtain import obtain
from .refine import refine
from .revert import revert
from .rewrite import rewrite, rw
from .simpl import dsimp, simpl, unfold
from .specialize import specialize
from .suffices import suffices

__all__ = [
    # 1. Forward Reasoning & Context
    "intro",
    "intros",
    "have",
    "obtain",
    "specialize",
    "revert",
    "clear",
    # 2. Backward Reasoning & Goal Reduction
    "apply",
    "exact",
    "refine",
    "assumption",
    "suffices",
    "constructor",
    "left",
    "right",
    "split",
    "use",
    "exists",
    # 3. Destructuring & Case Analysis
    "CasesPatterns",
    "RCasesPattern",
    "cases",
    "rcases",
    "induction",
    # 4. Equality, Reduction & Unfolding
    "reflexivity",
    "rfl",
    "symmetry",
    "symm",
    "transitivity",
    "trans",
    "rewrite",
    "rw",
    "unfold",
    "simpl",
    "dsimp",
    "change",
    # 5. Automation, Contradiction & Decision
    "contradiction",
    "exfalso",
]
