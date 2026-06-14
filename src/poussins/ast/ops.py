"""
Functional operations over ProofTerm AST nodes.
"""
from __future__ import annotations

from copy import deepcopy

from .proof_terms import (
    ProofTerm,
    PMetaVar,
    PVar,
    PLam,
    PApp,
    PAndI,
    PAndEL,
    PAndER,
    POrIL,
    POrIR,
    PTrueI,
    POrE,
    PFalseE,
    PExI,
    PExE,
)


def has_meta_var(term: ProofTerm) -> bool:
    """Return True when the proof term contains at least one meta-variable."""
    return bool(collect_meta_var_ids(term))


def collect_meta_var_ids(term: ProofTerm) -> set[str]:
    """Collect all meta-variable ids appearing in a proof term."""
    match term:
        case PMetaVar(goal_id):
            return {goal_id}
        case PVar(_):
            return set()
        case PLam(_, _, body):
            return collect_meta_var_ids(body)
        case PApp(fn, arg):
            return collect_meta_var_ids(fn) | collect_meta_var_ids(arg)
        case PAndI(left, right):
            return collect_meta_var_ids(left) | collect_meta_var_ids(right)
        case PAndEL(inner):
            return collect_meta_var_ids(inner)
        case PAndER(inner):
            return collect_meta_var_ids(inner)
        case POrIL(proof, _):
            return collect_meta_var_ids(proof)
        case POrIR(_, proof):
            return collect_meta_var_ids(proof)
        case PTrueI():
            return set()
        case POrE(disj_proof, _, left_case, _, right_case):
            return (
                collect_meta_var_ids(disj_proof)
                | collect_meta_var_ids(left_case)
                | collect_meta_var_ids(right_case)
            )
        case PFalseE(inner, _):
            return collect_meta_var_ids(inner)
        case PExI(_, _, _, proof):
            return collect_meta_var_ids(proof)
        case PExE(exists_proof, _, _, case_proof):
            return collect_meta_var_ids(exists_proof) | collect_meta_var_ids(case_proof)
        case _:
            raise NotImplementedError(f"Unknown proof term: {term}")


def substitute_meta_var(term: ProofTerm, goal_id: str, assignment: ProofTerm) -> ProofTerm:
    """Recursively replace goal_id meta-variable with assignment in term."""
    match term:
        case PMetaVar(current_goal_id):
            if current_goal_id == goal_id:
                return deepcopy(assignment)
            return term
        case PVar(_):
            return term
        case PLam(var, dom, body):
            return PLam(var, dom, substitute_meta_var(body, goal_id, assignment))
        case PApp(fn, arg):
            return PApp(
                fn=substitute_meta_var(fn, goal_id, assignment),
                arg=substitute_meta_var(arg, goal_id, assignment),
            )
        case PAndI(left, right):
            return PAndI(
                left=substitute_meta_var(left, goal_id, assignment),
                right=substitute_meta_var(right, goal_id, assignment),
            )
        case PAndEL(inner):
            return PAndEL(substitute_meta_var(inner, goal_id, assignment))
        case PAndER(inner):
            return PAndER(substitute_meta_var(inner, goal_id, assignment))
        case POrIL(proof, other_disjunct):
            return POrIL(substitute_meta_var(proof, goal_id, assignment), other_disjunct)
        case POrIR(other_disjunct, proof):
            return POrIR(other_disjunct, substitute_meta_var(proof, goal_id, assignment))
        case PTrueI():
            return term
        case POrE(disj_proof, left_hyp, left_case, right_hyp, right_case):
            return POrE(
                disj_proof=substitute_meta_var(disj_proof, goal_id, assignment),
                left_hyp=left_hyp,
                left_case=substitute_meta_var(left_case, goal_id, assignment),
                right_hyp=right_hyp,
                right_case=substitute_meta_var(right_case, goal_id, assignment),
            )
        case PFalseE(inner, conclusion):
            return PFalseE(
                inner=substitute_meta_var(inner, goal_id, assignment),
                conclusion=conclusion,
            )
        case PExI(exists_var, body, witness, proof):
            return PExI(
                exists_var=exists_var,
                body=body,
                witness=witness,
                proof=substitute_meta_var(proof, goal_id, assignment),
            )
        case PExE(exists_proof, prop_var, hyp_var, case_proof):
            return PExE(
                exists_proof=substitute_meta_var(exists_proof, goal_id, assignment),
                prop_var=prop_var,
                hyp_var=hyp_var,
                case_proof=substitute_meta_var(case_proof, goal_id, assignment),
            )
        case _:
            raise NotImplementedError(f"Unknown proof term: {term}")
