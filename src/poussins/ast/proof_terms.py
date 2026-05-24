"""ProofTerm AST nodes for propositional logic (natural deduction).

Each node corresponds to one natural deduction inference rule.

Inference rules covered:
    PVar      Var     h : A in ctx  =>  ctx |- A
    PLam      ->-I    ctx, x:A |- B  =>  ctx |- A -> B
    PApp      ->-E    ctx |- A -> B,  ctx |- A  =>  ctx |- B
    PAndI     /\\-I   ctx |- A,  ctx |- B  =>  ctx |- A /\\ B
    PAndE1    /\\-E1  ctx |- A /\\ B  =>  ctx |- A
    PAndE2    /\\-E2  ctx |- A /\\ B  =>  ctx |- B
    POrIL     \\/-I1  ctx |- A  =>  ctx |- A \\/ B
    POrIR     \\/-I2  ctx |- B  =>  ctx |- A \\/ B
    POrE      \\/-E   ctx |- A \\/ B, ctx,h:A |- C, ctx,h:B |- C  =>  ctx |- C
    PTrueI    T-I     ctx |- True
    PFalseE   F-E     ctx |- False  =>  ctx |- A  (ex falso)
    PExI      ∃-I     ctx |- P[A/x]  =>  ctx |- ∃x. P
    PExE      ∃-E     ctx |- ∃x. P,  ctx, h:P[α/x] |- C  =>  ctx |- C

Note on negation: FNot is not a primitive node.
    ~A is sugar for FImpl(A, FFalse), expanded during formula parsing
    from formula text to Formula AST.
    PNotI = PLam,  PNotE = PApp  (no extra nodes needed).

TODO:
- Add PRefl once FEq and a Term AST are introduced.
- Add oracle proof terms (PRing, PSimp, POmega) via reflection.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass

from .formulas import Formula


class ProofTerm(ABC):
    @property
    @abstractmethod
    def has_meta_var(self) -> bool:
        pass


@dataclass()
class PMetaVar(ProofTerm):
    """Meta-variable (proof hole): represents an unresolved subgoal in the proof tree."""

    goal_id: str

    @property
    def has_meta_var(self) -> bool:
        return True


@dataclass()
class PVar(ProofTerm):
    """Hypothesis variable: proves A when h : A is in context."""

    name: str

    @property
    def has_meta_var(self) -> bool:
        return False


@dataclass()
class PLam(ProofTerm):
    """Implication introduction: abstracts over a hypothesis.

    Proves antecedent -> consequent when body proves consequent
    under the assumption var : dom (= antecedent).
    """

    var: str
    dom: Formula
    body: ProofTerm

    @property
    def has_meta_var(self) -> bool:
        return self.body.has_meta_var


@dataclass()
class PApp(ProofTerm):
    """Implication elimination (modus ponens)."""

    fn: ProofTerm
    arg: ProofTerm

    @property
    def has_meta_var(self) -> bool:
        return self.fn.has_meta_var or self.arg.has_meta_var


@dataclass()
class PAndI(ProofTerm):
    """Conjunction introduction."""

    left: ProofTerm
    right: ProofTerm

    @property
    def has_meta_var(self) -> bool:
        return self.left.has_meta_var or self.right.has_meta_var


@dataclass()
class PAndE1(ProofTerm):
    """Conjunction elimination, left projection."""

    inner: ProofTerm

    @property
    def has_meta_var(self) -> bool:
        return self.inner.has_meta_var


@dataclass()
class PAndE2(ProofTerm):
    """Conjunction elimination, right projection."""

    inner: ProofTerm

    @property
    def has_meta_var(self) -> bool:
        return self.inner.has_meta_var


@dataclass()
class POrIL(ProofTerm):
    """Disjunction introduction, left.

    right_type must be provided explicitly because type_check cannot
    infer the right disjunct from the proof term alone.
    """

    pf: ProofTerm
    right_type: Formula

    @property
    def has_meta_var(self) -> bool:
        return self.pf.has_meta_var

@dataclass()
class POrIR(ProofTerm):
    """Disjunction introduction, right."""

    left_type: Formula
    pf: ProofTerm

    @property
    def has_meta_var(self) -> bool:
        return self.pf.has_meta_var


@dataclass()
class PTrueI(ProofTerm):
    """True introduction: proves FTrue unconditionally."""

    @property
    def has_meta_var(self) -> bool:
        return False


@dataclass()
class POrE(ProofTerm):
    """Disjunction elimination (case split).

    Given a proof of A \\/ B, and a proof of C assuming A (left branch),
    and a proof of C assuming B (right branch), concludes C.

    left_var  : name bound in left_branch  (h : A)
    right_var : name bound in right_branch (h : B)
    """

    disj: ProofTerm
    left_var: str
    left_branch: ProofTerm
    right_var: str
    right_branch: ProofTerm

    @property
    def has_meta_var(self) -> bool:
        return (
            self.disj.has_meta_var or
            self.left_branch.has_meta_var or
            self.right_branch.has_meta_var
        )


@dataclass()
class PFalseE(ProofTerm):
    """False elimination (ex falso quodlibet): proves any formula from FFalse."""

    inner: ProofTerm
    conclusion: Formula

    @property
    def has_meta_var(self) -> bool:
        return self.inner.has_meta_var


@dataclass()
class PExI(ProofTerm):
    """Existential introduction (∃-I).

    Proves FExists(exists_var, body) when pf proves body[witness/exists_var].
    Both exists_var and body must be provided because the type checker cannot
    infer them from the proof term alone.
    """

    exists_var: str
    body: Formula
    witness: Formula
    pf: ProofTerm

    @property
    def has_meta_var(self) -> bool:
        return self.pf.has_meta_var


@dataclass()
class PExE(ProofTerm):
    """Existential elimination (∃-E).

    Given pf : ∃x. P(x), introduces a fresh propositional variable prop_var
    and a hypothesis hyp_var : P[prop_var/x], then proves the conclusion C
    (which must not mention prop_var).

    prop_var  : name of the fresh propositional variable (appears in hyp type)
    hyp_var   : proof-context name bound to P[prop_var/x]
    """

    pf: ProofTerm
    prop_var: str
    hyp_var: str
    body: ProofTerm

    @property
    def has_meta_var(self) -> bool:
        return self.pf.has_meta_var or self.body.has_meta_var
