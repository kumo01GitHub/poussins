"""
Kernel-level proof term inference and type checking.
"""
from __future__ import annotations

from .goal import Context
from ..ast import (
    ProofTerm,
    PMetaVar,
    PVar,
    PLam,
    PApp,
    PAndI,
    PAndE,
    POrIL,
    POrIR,
    PTrueI,
    POrE,
    PFalseE,
    PForallI,
    PForallE,
    PExI,
    PExE,
    PRefl,
    Expr,
    EImp,
    EAnd,
    EOr,
    ETop,
    EBot,
    EEq,
    EForall,
    EExists,
    EVar,
    EApp,
    FunctionSymbol,
    Sort,
)
from ..errors import KernelTypeError


def _resolve_fn_symbol(context: Context, name: str) -> FunctionSymbol | None:
    return context.fn_symbols.get(name)


def _ensure_declared_sort(sort, context: Context):
    if not context.is_declared_sort(sort):
        raise KernelTypeError(f"Undeclared sort '{sort}'. Register it in Context.add_sorts first.")


def infer_term_sort(term: Expr, context: Context):
    match term:
        case EVar(name):
            sort = context.get_term_sort(name)
            if sort is None:
                raise KernelTypeError(f"Unknown term variable '{name}'.")
            _ensure_declared_sort(sort, context)
            return sort
        case EApp(name, args):
            symbol = _resolve_fn_symbol(context, name)
            if symbol is None:
                raise KernelTypeError(f"Unknown function symbol '{name}'.")
            _ensure_declared_sort(symbol.result_sort, context)
            if len(args) != len(symbol.arg_sorts):
                raise KernelTypeError(
                    f"Function '{name}' expects {len(symbol.arg_sorts)} arguments, got {len(args)}."
                )
            for idx, (arg, expected_sort) in enumerate(zip(args, symbol.arg_sorts, strict=True)):
                _ensure_declared_sort(expected_sort, context)
                actual_sort = infer_term_sort(arg, context)
                if actual_sort != expected_sort:
                    raise KernelTypeError(
                        f"Function '{name}' argument {idx + 1} sort mismatch: "
                        f"expected {expected_sort}, got {actual_sort}."
                    )
            return symbol.result_sort
        case _:
            raise NotImplementedError(f"Unknown term: {term}")


def _subst_term_in_term(term: Expr, var_name: str, replacement: Expr) -> Expr:
    match term:
        case EVar(name):
            return replacement if name == var_name else term
        case EApp(name, args):
            return EApp(name, tuple(_subst_term_in_term(arg, var_name, replacement) for arg in args))
        case _:
            raise NotImplementedError(f"Unknown term: {term}")


def _subst_term_in_expr(formula: Expr, var_name: str, replacement: Expr) -> Expr:
    match formula:
        case EVar(_):
            return formula
        case EApp(name, args):
            return EApp(name, tuple(_subst_term_in_term(arg, var_name, replacement) for arg in args))
        case EEq(left, right):
            return EEq(
                _subst_term_in_term(left, var_name, replacement),
                _subst_term_in_term(right, var_name, replacement),
            )
        case EImp(antecedent, consequent):
            return EImp(
                _subst_term_in_expr(antecedent, var_name, replacement),
                _subst_term_in_expr(consequent, var_name, replacement),
            )
        case EAnd(left, right):
            return EAnd(
                _subst_term_in_expr(left, var_name, replacement),
                _subst_term_in_expr(right, var_name, replacement),
            )
        case EOr(left, right):
            return EOr(
                _subst_term_in_expr(left, var_name, replacement),
                _subst_term_in_expr(right, var_name, replacement),
            )
        case ETop() | EBot():
            return formula
        case EForall(bound_var, _, body) | EExists(bound_var, _, body):
            if bound_var == var_name:
                return formula
            if isinstance(formula, EForall):
                return EForall(formula.var, formula.sort, _subst_term_in_expr(body, var_name, replacement))
            return EExists(formula.var, formula.sort, _subst_term_in_expr(body, var_name, replacement))
        case _:
            raise NotImplementedError(f"Unknown formula: {formula}")


def _contains_term_var_in_term(term: Expr, var_name: str) -> bool:
    match term:
        case EVar(name):
            return name == var_name
        case EApp(_, args):
            return any(_contains_term_var_in_term(arg, var_name) for arg in args)
        case _:
            raise NotImplementedError(f"Unknown term: {term}")


def _contains_term_var(formula: Expr, var_name: str) -> bool:
    match formula:
        case EVar(_):
            return False
        case EApp(_, args):
            return any(_contains_term_var_in_term(arg, var_name) for arg in args)
        case EEq(left, right):
            return _contains_term_var_in_term(left, var_name) or _contains_term_var_in_term(right, var_name)
        case EImp(antecedent, consequent):
            return _contains_term_var(antecedent, var_name) or _contains_term_var(consequent, var_name)
        case EAnd(left, right) | EOr(left, right):
            return _contains_term_var(left, var_name) or _contains_term_var(right, var_name)
        case ETop() | EBot():
            return False
        case EForall(bound_var, _, body) | EExists(bound_var, _, body):
            if bound_var == var_name:
                return False
            return _contains_term_var(body, var_name)
        case _:
            raise NotImplementedError(f"Unknown formula: {formula}")


def _ensure_well_formed_expr(formula: Expr, context: Context):
    match formula:
        case EVar(_):
            return
        case EApp(name, args):
            symbol = _resolve_fn_symbol(context, name)
            if symbol is None:
                raise KernelTypeError(f"Unknown symbol '{name}'.")
            if symbol.result_sort != "Prop":
                raise KernelTypeError(f"Symbol '{name}' must return Prop in proposition position.")
            if len(args) != len(symbol.arg_sorts):
                raise KernelTypeError(
                    f"Symbol '{name}' expects {len(symbol.arg_sorts)} arguments, got {len(args)}."
                )
            for idx, (arg, expected_sort) in enumerate(zip(args, symbol.arg_sorts, strict=True)):
                _ensure_declared_sort(expected_sort, context)
                actual_sort = infer_term_sort(arg, context)
                if actual_sort != expected_sort:
                    raise KernelTypeError(
                        f"Symbol '{name}' argument {idx + 1} sort mismatch: "
                        f"expected {expected_sort}, got {actual_sort}."
                    )
            return
        case EEq(left, right):
            left_sort = infer_term_sort(left, context)
            right_sort = infer_term_sort(right, context)
            if left_sort != right_sort:
                raise KernelTypeError("Equality requires both sides to have the same sort.")
            return
        case EImp(antecedent, consequent):
            _ensure_well_formed_expr(antecedent, context)
            _ensure_well_formed_expr(consequent, context)
            return
        case EAnd(left, right) | EOr(left, right):
            _ensure_well_formed_expr(left, context)
            _ensure_well_formed_expr(right, context)
            return
        case ETop() | EBot():
            return
        case EForall(var, sort, body) | EExists(var, sort, body):
            _ensure_declared_sort(sort, context)
            _ensure_well_formed_expr(body, context.add_terms({var: sort}))
            return
        case _:
            raise NotImplementedError(f"Unknown formula: {formula}")


def infer_expr(term: ProofTerm, context: Context) -> Expr:
    """Infer the formula proven by a proof term in the given context."""
    match term:
        case PMetaVar(_):
            raise KernelTypeError("Cannot infer formula of a meta-variable.")
        case PVar(name):
            formula = context.get(name)
            if formula is None:
                raise KernelTypeError(f"Variable {name} not found in context.")
            _ensure_well_formed_expr(formula, context)
            return formula
        case PLam(var, dom, body):
            _ensure_well_formed_expr(dom, context)
            return EImp(dom, infer_expr(body, context.add({var: dom})))
        case PApp(fn, arg):
            fn_formula = infer_expr(fn, context)
            arg_formula = infer_expr(arg, context)
            if not isinstance(fn_formula, EImp):
                raise KernelTypeError("Cannot apply a non-function term.")
            if fn_formula.antecedent != arg_formula:
                raise KernelTypeError("Argument formula does not match function's domain.")
            return fn_formula.consequent
        case PAndI(left, right):
            return EAnd(infer_expr(left, context), infer_expr(right, context))
        case PAndE(conj_proof, left_hyp, right_hyp, case_proof):
            conj_formula = infer_expr(conj_proof, context)
            if not isinstance(conj_formula, EAnd):
                raise KernelTypeError("PAndE expects proof of a conjunction.")
            return infer_expr(case_proof, context.add({
                left_hyp: conj_formula.left,
                right_hyp: conj_formula.right
            }))
        case POrIL(proof, other_disjunct):
            _ensure_well_formed_expr(other_disjunct, context)
            return EOr(infer_expr(proof, context), other_disjunct)
        case POrIR(other_disjunct, proof):
            _ensure_well_formed_expr(other_disjunct, context)
            return EOr(other_disjunct, infer_expr(proof, context))
        case PTrueI():
            return ETop()
        case POrE(disj_proof, left_hyp, left_case, right_hyp, right_case):
            disj_formula = infer_expr(disj_proof, context)
            if not isinstance(disj_formula, EOr):
                raise KernelTypeError("POrE expects disjunction.")
            left_formula = infer_expr(left_case, context.add({left_hyp: disj_formula.left}))
            right_formula = infer_expr(right_case, context.add({right_hyp: disj_formula.right}))
            if left_formula != right_formula:
                raise KernelTypeError("Branches of POrE must yield the same formula.")
            return left_formula
        case PFalseE(inner, conclusion):
            if not isinstance(infer_expr(inner, context), EBot):
                raise KernelTypeError("PFalseE expects proof of False.")
            _ensure_well_formed_expr(conclusion, context)
            return conclusion
        case PForallI(var, sort, body):
            _ensure_declared_sort(sort, context)
            return EForall(var, sort, infer_expr(body, context.add_terms({var: sort})))
        case PForallE(forall_proof, witness):
            pf_formula = infer_expr(forall_proof, context)
            if not isinstance(pf_formula, EForall):
                raise KernelTypeError("PForallE expects proof of a universal formula.")
            witness_sort = infer_term_sort(witness, context)
            if witness_sort != pf_formula.sort:
                raise KernelTypeError("PForallE witness sort mismatch.")
            return _subst_term_in_expr(pf_formula.body, pf_formula.var, witness)
        case PExI(exists_var, sort, body, witness, proof):
            _ensure_declared_sort(sort, context)
            witness_sort = infer_term_sort(witness, context)
            if witness_sort != sort:
                raise KernelTypeError("PExI witness sort mismatch.")
            expected_pf_formula = _subst_term_in_expr(body, exists_var, witness)
            actual_pf_formula = infer_expr(proof, context)
            if actual_pf_formula != expected_pf_formula:
                raise KernelTypeError("PExI witness/body mismatch.")
            return EExists(exists_var, sort, body)
        case PExE(exists_proof, witness_var, hyp_var, case_proof):
            pf_formula = infer_expr(exists_proof, context)
            if not isinstance(pf_formula, EExists):
                raise KernelTypeError("PExE expects proof of an existential.")
            witness = EVar(witness_var)
            hyp_formula = _subst_term_in_expr(pf_formula.body, pf_formula.var, witness)
            conclusion = infer_expr(
                case_proof,
                context.add_terms({witness_var: pf_formula.sort}).add({hyp_var: hyp_formula}),
            )
            if _contains_term_var(conclusion, witness_var):
                raise KernelTypeError("PExE conclusion must not contain the witness variable.")
            return conclusion
        case PRefl(eq_term):
            infer_term_sort(eq_term, context)
            return EEq(eq_term, eq_term)
        case _:
            raise NotImplementedError(f"Unknown proof term: {term}")


def check_expr(term: ProofTerm, expected: Expr, context: Context) -> bool:
    """Return True when term checks against expected formula in context."""
    try:
        inferred = infer_expr(term, context)
        return inferred == expected or _expr_alpha_eq(inferred, expected)
    except KernelTypeError:
        return False


def _expr_alpha_eq(left: Expr, right: Expr) -> bool:
    match left, right:
        case EVar(left_name), EVar(right_name):
            return left_name == right_name
        case EApp(left_name, left_args), EApp(right_name, right_args):
            return left_name == right_name and left_args == right_args
        case EEq(left_l, left_r), EEq(right_l, right_r):
            return left_l == right_l and left_r == right_r
        case EImp(left_a, left_c), EImp(right_a, right_c):
            return _expr_alpha_eq(left_a, right_a) and _expr_alpha_eq(left_c, right_c)
        case EAnd(left_l, left_r), EAnd(right_l, right_r):
            return _expr_alpha_eq(left_l, right_l) and _expr_alpha_eq(left_r, right_r)
        case EOr(left_l, left_r), EOr(right_l, right_r):
            return _expr_alpha_eq(left_l, right_l) and _expr_alpha_eq(left_r, right_r)
        case ETop(), ETop():
            return True
        case EBot(), EBot():
            return True
        case EForall(left_var, left_sort, left_body), EForall(right_var, right_sort, right_body):
            if left_sort != right_sort:
                return False
            normalized_right = _subst_term_in_expr(right_body, right_var, EVar(left_var))
            return _expr_alpha_eq(left_body, normalized_right)
        case EExists(left_var, left_sort, left_body), EExists(right_var, right_sort, right_body):
            if left_sort != right_sort:
                return False
            normalized_right = _subst_term_in_expr(right_body, right_var, EVar(left_var))
            return _expr_alpha_eq(left_body, normalized_right)
        case _:
            return False
