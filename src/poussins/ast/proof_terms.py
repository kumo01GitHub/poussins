"""ProofTerm AST nodes for propositional logic (natural deduction).

Each node corresponds to one natural deduction inference rule.

Inference rules covered:
    PVar      Var     h : A in ctx  =>  ctx |- A
    PLam      ->-I    ctx, x:A |- B  =>  ctx |- A -> B
    PApp      ->-E    ctx |- A -> B,  ctx |- A  =>  ctx |- B
    PAndI     /\\-I   ctx |- A,  ctx |- B  =>  ctx |- A /\\ B
    PAndEL    /\\-EL  ctx |- A /\\ B  =>  ctx |- A
    PAndER    /\\-ER  ctx |- A /\\ B  =>  ctx |- B
    POrIL     \\/-IL  ctx |- A  =>  ctx |- A \\/ B
    POrIR     \\/-IR  ctx |- B  =>  ctx |- A \\/ B
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

from abc import ABC
from dataclasses import dataclass

from .formulas import Formula


class ProofTerm(ABC):
    """Abstract base class for proof terms."""
    pass


@dataclass(frozen=True)
class PMetaVar(ProofTerm):
    """Meta-variable (proof hole): represents an unresolved subgoal in the proof tree."""

    goal_id: str

    def __str__(self) -> str:
        return f"?{self.goal_id}"


@dataclass(frozen=True)
class PVar(ProofTerm):
    """Hypothesis variable: proves A when h : A is in context."""

    name: str

    def __str__(self) -> str:
        return self.name


@dataclass(frozen=True)
class PLam(ProofTerm):
    """Implication introduction: abstracts over a hypothesis.

    Proves antecedent -> consequent when body proves consequent
    under the assumption var : dom (= antecedent).
    """

    var: str
    dom: Formula
    body: ProofTerm

    def __str__(self) -> str:
        return f"(→I λ{self.var}: {self.dom}. {self.body})"


@dataclass(frozen=True)
class PApp(ProofTerm):
    """Implication elimination (modus ponens)."""

    fn: ProofTerm
    arg: ProofTerm

    def __str__(self) -> str:
        return f"(→E {self.fn}; {self.arg})"


@dataclass(frozen=True)
class PAndI(ProofTerm):
    """Conjunction introduction."""

    left: ProofTerm
    right: ProofTerm

    def __str__(self) -> str:
        return f"(∧I {self.left}; {self.right})"


@dataclass(frozen=True)
class PAndEL(ProofTerm):
    """Conjunction elimination, left projection."""

    inner: ProofTerm

    def __str__(self) -> str:
        return f"(∧EL {self.inner})"


@dataclass(frozen=True)
class PAndER(ProofTerm):
    """Conjunction elimination, right projection."""

    inner: ProofTerm

    def __str__(self) -> str:
        return f"(∧ER {self.inner})"


@dataclass(frozen=True)
class POrIL(ProofTerm):
    """Disjunction introduction, left.

    other_disjunct must be provided explicitly because type_check cannot
    infer the right disjunct from the proof term alone.
    """

    proof: ProofTerm
    other_disjunct: Formula

    def __str__(self) -> str:
        return f"(∨IL {self.proof} : _ ∨ {self.other_disjunct})"


@dataclass(frozen=True)
class POrIR(ProofTerm):
    """Disjunction introduction, right."""

    other_disjunct: Formula
    proof: ProofTerm

    def __str__(self) -> str:
        return f"(∨IR {self.proof} : {self.other_disjunct} ∨ _)"


@dataclass(frozen=True)
class PTrueI(ProofTerm):
    """True introduction: proves FTrue unconditionally."""

    def __str__(self) -> str:
        return "⊤I"


@dataclass(frozen=True)
class POrE(ProofTerm):
    """Disjunction elimination (case split).

    Given a proof of A \\/ B, and a proof of C assuming A (left branch),
    and a proof of C assuming B (right branch), concludes C.

    left_hyp  : name bound in left_case  (h : A)
    right_hyp : name bound in right_case (h : B)
    """

    disj_proof: ProofTerm
    left_hyp: str
    left_case: ProofTerm
    right_hyp: str
    right_case: ProofTerm

    def __str__(self) -> str:
        return (
            f"(∨E {self.disj_proof}; "
            f"{self.left_hyp} ↦ {self.left_case}; "
            f"{self.right_hyp} ↦ {self.right_case})"
        )


@dataclass(frozen=True)
class PFalseE(ProofTerm):
    """False elimination (ex falso quodlibet): proves any formula from FFalse."""

    inner: ProofTerm
    conclusion: Formula

    def __str__(self) -> str:
        return f"(⊥E {self.inner} : {self.conclusion})"


@dataclass(frozen=True)
class PExI(ProofTerm):
    """Existential introduction (∃-I).

    Proves FExists(exists_var, body) when proof proves body[witness/exists_var].
    Both exists_var and body must be provided because the type checker cannot
    infer them from the proof term alone.
    """

    exists_var: str
    body: Formula
    witness: Formula
    proof: ProofTerm

    def __str__(self) -> str:
        return f"(∃I {self.exists_var} := {self.witness}; {self.proof} : ∃{self.exists_var}. {self.body})"


@dataclass(frozen=True)
class PExE(ProofTerm):
    """Existential elimination (∃-E).

    Given exists_proof : ∃x. P(x), introduces a fresh propositional variable prop_var
    and a hypothesis hyp_var : P[prop_var/x], then proves the conclusion C
    (which must not mention prop_var).

    prop_var  : name of the fresh propositional variable (appears in hyp type)
    hyp_var   : proof-context name bound to P[prop_var/x]
    """

    exists_proof: ProofTerm
    prop_var: str
    hyp_var: str
    case_proof: ProofTerm

    def __str__(self) -> str:
        return f"(∃E {self.exists_proof}; {self.prop_var}, {self.hyp_var} ↦ {self.case_proof})"
