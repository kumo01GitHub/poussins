"""Framework-level base class providing method-style tactic access for Theorems."""
from __future__ import annotations

import functools
from abc import ABC, abstractmethod
from collections.abc import Callable
from logging import Logger
from typing import Concatenate, Final

from ..ast import EVar, Expr
from ..environment import Environment, TheoremDeclaration
from ..kernel import ProofManager, ProofState
from ..tactics import (
    CasesPatterns,
    RCasesPattern,
    apply,
    assumption,
    cases,
    change,
    clear,
    constructor,
    contradiction,
    dsimp,
    exact,
    exfalso,
    exists,
    have,
    induction,
    intro,
    intros,
    left,
    obtain,
    rcases,
    refine,
    reflexivity,
    revert,
    rewrite,
    rfl,
    right,
    rw,
    simpl,
    specialize,
    split,
    suffices,
    symm,
    symmetry,
    trans,
    transitivity,
    unfold,
    use,
)
from .declared_type import DeclaredType
from .prop import Prop

type ExprLike = Expr | Prop | DeclaredType | str


def log_tactic[**TacticParams](
    func: Callable[Concatenate[ProofScript, TacticParams], None]
) -> Callable[Concatenate[ProofScript, TacticParams], None]:
    """Log the execution of a tactic method in ProofScript."""

    @functools.wraps(func)
    def wrapper(
        self: ProofScript,
        *args: TacticParams.args,
        **kwargs: TacticParams.kwargs
    ) -> None:
        self.logger.info(f"Executing '{func.__name__}' tactic with: {args} {kwargs}")

        result = func(self, *args, **kwargs)

        self.logger.info(f"After '{func.__name__}'")
        current_goal = self.current_state.current_goal
        if current_goal is None:
            self.logger.info("==> None (proof is closed)")
        else:
            self.logger.info(f"==> Current goal ID: {current_goal.id}")
            self.logger.info(f"    {current_goal.statement}")
            self.logger.info("-" * 50)
            if current_goal.local_context:
                for name, expr in current_goal.local_context.items():
                    self.logger.info(f"    {name}: {expr}")

        return result

    return wrapper


class ProofScript(ABC):
    """Abstract base class for all proof-carrying script objects (Theorem, Example).

    This class acts purely as a fluent frontend interface for writing proof scripts.
    It completely delegates all state mutation and
    history tracking concerns to ProofManager.
    """

    logger: Logger

    def __init__(self, statement: Expr, env: Environment):
        """Create a proof script bound to a statement and environment."""
        self.statement: Final[Expr] = statement
        self.env: Final[Environment] = env
        self.manager: Final[ProofManager] = ProofManager(statement, env)

    @property
    def current_state(self) -> ProofState:
        """Return the current proof state."""
        return self.manager.current_state

    @property
    def is_closed(self) -> bool:
        """Return whether the proof has no remaining goals."""
        return self.manager.is_closed

    def undo(self):
        """Revert the proof to the previous state."""
        self.manager.undo()

    @abstractmethod
    def qed(self) -> TheoremDeclaration | None:
        """Finalize the proof script."""
        pass

    def _to_expr(self, term: ExprLike) -> Expr:
        if isinstance(term, Expr):
            return term
        elif isinstance(term, Prop):
            return Prop.to_expr(term)
        elif isinstance(term, DeclaredType):
            return DeclaredType.to_expr(term)
        elif isinstance(term, str):
            return EVar(term)

    # ------------------------------------------------------------------
    #  1. Forward Reasoning & Context
    # ------------------------------------------------------------------

    @log_tactic
    def intro(self, as_: str) -> None:
        """Introduce a hypothesis with the given name into the local context."""
        intro(self.manager, as_)

    @log_tactic
    def intros(self, as_: list[str]) -> None:
        """Introduce multiple hypotheses into the local context."""
        intros(self.manager, as_)

    @log_tactic
    def have(self, as_: str, type: ExprLike) -> None:
        """Introduce an intermediate assertion (have h : P)."""
        have(self.manager, as_, self._to_expr(type))

    @log_tactic
    def obtain(self, pattern: RCasesPattern, via: ExprLike) -> None:
        """Introduce a new witness and immediately destructure it using rcases."""
        obtain(self.manager, pattern, self._to_expr(via))

    @log_tactic
    def specialize(self, at: str, via: ExprLike) -> None:
        """Specialize a hypothesis in the local context with an argument."""
        specialize(self.manager, at, self._to_expr(via))

    @log_tactic
    def revert(self, at: str | list[str]) -> None:
        """Revert one or more hypotheses from the local context back into the goal."""
        revert(self.manager, at)

    @log_tactic
    def clear(self, at: str) -> None:
        """Remove a local hypothesis from the current goal context."""
        clear(self.manager, at)

    # ------------------------------------------------------------------
    # 2. Backward Reasoning & Goal Reduction
    # ------------------------------------------------------------------

    @log_tactic
    def apply(self, via: ExprLike) -> None:
        """Apply a theorem, hypothesis, or expression to the current goal."""
        apply(self.manager, self._to_expr(via))

    @log_tactic
    def exact(self, via: ExprLike) -> None:
        """Close the current goal with the given expression."""
        exact(self.manager, self._to_expr(via))

    @log_tactic
    def refine(self, expr: Expr) -> None:
        """Refine current goal using an expression that may contain metavariables."""
        refine(self.manager, expr)

    @log_tactic
    def assumption(self) -> None:
        """Solve the current goal using a matching hypothesis."""
        assumption(self.manager)

    @log_tactic
    def suffices(self, as_: str, type: ExprLike) -> None:
        """Introduce an intermediate assertion (suffices h : P)."""
        suffices(self.manager, as_, self._to_expr(type))

    @log_tactic
    def constructor(self, index: int | None = None) -> None:
        """Apply an inductive constructor to the current goal."""
        constructor(self.manager, index)

    @log_tactic
    def left(self) -> None:
        """Select the left branch of a disjunction goal."""
        left(self.manager)

    @log_tactic
    def right(self) -> None:
        """Select the right branch of a disjunction goal."""
        right(self.manager)

    @log_tactic
    def split(self) -> None:
        """Split a conjunction goal into two subgoals."""
        split(self.manager)

    @log_tactic
    def use(self, via: ExprLike) -> None:
        """Refine the current goal of the form `Exists A P` by providing a witness."""
        use(self.manager, self._to_expr(via))

    @log_tactic
    def exists(self, via: ExprLike) -> None:
        """Refine the current goal of the form `Exists A P` by providing a witness."""
        exists(self.manager, self._to_expr(via))

    # ------------------------------------------------------------------
    # 3. Destructuring & Case Analysis
    # ------------------------------------------------------------------

    @log_tactic
    def cases(self, at: str, with_: CasesPatterns = None ) -> None:
        """Case-split on an inductive hypothesis."""
        cases(self.manager, at, with_)

    @log_tactic
    def rcases(self, at, with_: RCasesPattern) -> None:
        """Destruct a hypothesis recursively using a nested pattern structure."""
        rcases(self.manager, at, with_)

    @log_tactic
    def induction(self, at: str) -> None:
        """Perform induction on a hypothesis in the local context."""
        induction(self.manager, at)

    # ------------------------------------------------------------------
    # 4. Equality, Reduction & Unfolding
    # ------------------------------------------------------------------

    @log_tactic
    def reflexivity(self) -> None:
        """Solve the current goal if it is an equality of definitionally equal terms."""
        reflexivity(self.manager)

    @log_tactic
    def rfl(self) -> None:
        """Solve the current goal if it is an equality of definitionally equal terms."""
        rfl(self.manager)

    @log_tactic
    def symmetry(self) -> None:
        """Swap the left and right sides of an equality goal."""
        symmetry(self.manager)

    @log_tactic
    def symm(self) -> None:
        """Swap the left and right sides of an equality goal."""
        symm(self.manager)

    @log_tactic
    def transitivity(self, via: ExprLike) -> None:
        """Split an equality goal into two subgoals using a middle term."""
        transitivity(self.manager, self._to_expr(via))

    @log_tactic
    def trans(self, via: ExprLike) -> None:
        """Split an equality goal into two subgoals using a middle term."""
        trans(self.manager, self._to_expr(via))

    @log_tactic
    def rewrite(
        self,
        via: ExprLike,
        *,
        symm: bool = False,
        at: str | None = None,
        on: ExprLike | None = None,
    ) -> None:
        """Rewrite occurrences of LHS with RHS in current goal using hypothesis."""
        rewrite(
            self.manager,
            self._to_expr(via),
            symm,
            at,
            self._to_expr(on) if on is not None else None,
        )

    @log_tactic
    def rw(
        self,
        via: ExprLike,
        *,
        symm: bool = False,
        at: str | None = None,
        on: ExprLike | None = None,
    ) -> None:
        """Rewrite occurrences of LHS with RHS in current goal using hypothesis."""
        rw(
            self.manager,
            self._to_expr(via),
            symm,
            at,
            self._to_expr(on) if on is not None else None,
        )

    @log_tactic
    def unfold(self, def_name: str, *, at: str | None = None) -> None:
        """Unfold a specific definition in the current goal or hypothesis."""
        unfold(self.manager, def_name, at)

    @log_tactic
    def simpl(
        self,
        *,
        at: str | None = None,
        unfolding: set[str] | None = None
    ) -> None:
        """Simplify the current goal using definitional unfolding."""
        simpl(self.manager, at, unfolding)

    @log_tactic
    def dsimp(
        self,
        *,
        at: str | None = None,
        unfolding: set[str] | None = None
    ) -> None:
        """Definitional simplify without expanding unnecessary definitions."""
        dsimp(self.manager, at, unfolding)

    @log_tactic
    def change(self, via: ExprLike, *, at: str | None = None) -> None:
        """Replace the current goal with a definitionally equal expression."""
        change(self.manager, self._to_expr(via), at)

    # ------------------------------------------------------------------
    # 5. Automation, Contradiction & Decision
    # -----------------------------------------------------------------

    @log_tactic
    def exfalso(self) -> None:
        """Switch the current goal to False."""
        exfalso(self.manager)

    @log_tactic
    def contradiction(self) -> None:
        """Close the current goal if local hypotheses contain a contradiction."""
        contradiction(self.manager)
