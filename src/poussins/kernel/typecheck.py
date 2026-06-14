"""Kernel-level proof term inference and type checking."""

from __future__ import annotations

from poussins.ast import (
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
    Formula,
    FImpl,
    FAnd,
    FOr,
    FTrue,
    FFalse,
    FExists,
    FVar,
)
from poussins.errors import KernelTypeError
from .goal import Context


def _subst_formula_var(formula: Formula, var_name: str, replacement: Formula) -> Formula:
    """Capture-avoiding substitution for propositional variable names."""
    match formula:
        case FVar(name):
            return replacement if name == var_name else formula
        case FImpl(antecedent, consequent):
            return FImpl(
                _subst_formula_var(antecedent, var_name, replacement),
                _subst_formula_var(consequent, var_name, replacement),
            )
        case FAnd(left, right):
            return FAnd(
                _subst_formula_var(left, var_name, replacement),
                _subst_formula_var(right, var_name, replacement),
            )
        case FOr(left, right):
            return FOr(
                _subst_formula_var(left, var_name, replacement),
                _subst_formula_var(right, var_name, replacement),
            )
        case FTrue() | FFalse():
            return formula
        case FExists(bound_var, body):
            if bound_var == var_name:
                return formula
            return FExists(bound_var, _subst_formula_var(body, var_name, replacement))
        case _:
            raise NotImplementedError(f"Unknown formula: {formula}")


def _contains_formula_var(formula: Formula, var_name: str) -> bool:
    """Return True when var_name occurs free in formula."""
    match formula:
        case FVar(name):
            return name == var_name
        case FImpl(antecedent, consequent):
            return _contains_formula_var(antecedent, var_name) or _contains_formula_var(consequent, var_name)
        case FAnd(left, right) | FOr(left, right):
            return _contains_formula_var(left, var_name) or _contains_formula_var(right, var_name)
        case FTrue() | FFalse():
            return False
        case FExists(bound_var, body):
            if bound_var == var_name:
                return False
            return _contains_formula_var(body, var_name)
        case _:
            raise NotImplementedError(f"Unknown formula: {formula}")


def infer_formula(term: ProofTerm, context: Context) -> Formula:
    """Infer the formula proven by a proof term in the given context."""
    match term:
        case PMetaVar(_):
            raise KernelTypeError("Cannot infer formula of a meta-variable.")
        case PVar(name):
            formula = context.get(name)
            if formula is None:
                raise KernelTypeError(f"Variable {name} not found in context.")
            return formula
        case PLam(var, dom, body):
            return FImpl(dom, infer_formula(body, context.add({var: dom})))
        case PApp(fn, arg):
            fn_formula = infer_formula(fn, context)
            arg_formula = infer_formula(arg, context)
            if not isinstance(fn_formula, FImpl):
                raise KernelTypeError("Cannot apply a non-function term.")
            if fn_formula.antecedent != arg_formula:
                raise KernelTypeError("Argument formula does not match function's domain.")
            return fn_formula.consequent
        case PAndI(left, right):
            return FAnd(infer_formula(left, context), infer_formula(right, context))
        case PAndEL(inner):
            inner_formula = infer_formula(inner, context)
            if not isinstance(inner_formula, FAnd):
                raise KernelTypeError("PAndEL expects conjunction.")
            return inner_formula.left
        case PAndER(inner):
            inner_formula = infer_formula(inner, context)
            if not isinstance(inner_formula, FAnd):
                raise KernelTypeError("PAndER expects conjunction.")
            return inner_formula.right
        case POrIL(proof, other_disjunct):
            return FOr(infer_formula(proof, context), other_disjunct)
        case POrIR(other_disjunct, proof):
            return FOr(other_disjunct, infer_formula(proof, context))
        case PTrueI():
            return FTrue()
        case POrE(disj_proof, left_hyp, left_case, right_hyp, right_case):
            disj_formula = infer_formula(disj_proof, context)
            if not isinstance(disj_formula, FOr):
                raise KernelTypeError("POrE expects disjunction.")
            left_formula = infer_formula(left_case, context.add({left_hyp: disj_formula.left}))
            right_formula = infer_formula(right_case, context.add({right_hyp: disj_formula.right}))
            if left_formula != right_formula:
                raise KernelTypeError("Branches of POrE must yield the same formula.")
            return left_formula
        case PFalseE(inner, conclusion):
            if not isinstance(infer_formula(inner, context), FFalse):
                raise KernelTypeError("PFalseE expects proof of False.")
            return conclusion
        case PExI(exists_var, body, witness, proof):
            expected_pf_formula = _subst_formula_var(body, exists_var, witness)
            actual_pf_formula = infer_formula(proof, context)
            if actual_pf_formula != expected_pf_formula:
                raise KernelTypeError("PExI witness/body mismatch.")
            return FExists(exists_var, body)
        case PExE(exists_proof, prop_var, hyp_var, case_proof):
            pf_formula = infer_formula(exists_proof, context)
            if not isinstance(pf_formula, FExists):
                raise KernelTypeError("PExE expects proof of an existential.")
            hyp_formula = _subst_formula_var(pf_formula.body, pf_formula.var, FVar(prop_var))
            conclusion = infer_formula(case_proof, context.add({hyp_var: hyp_formula}))
            if _contains_formula_var(conclusion, prop_var):
                raise KernelTypeError("PExE conclusion must not contain the witness variable.")
            return conclusion
        case _:
            raise NotImplementedError(f"Unknown proof term: {term}")


def check_formula(term: ProofTerm, expected: Formula, context: Context) -> bool:
    """Return True when term checks against expected formula in context."""
    try:
        return infer_formula(term, context) == expected
    except KernelTypeError:
        return False
