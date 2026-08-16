import pytest

from poussins.ast import (
    EApp,
    EConst,
    ELam,
    EMatch,
    EMetaVar,
    EPi,
    Expr,
    ESort,
    EVar,
    UnivLevelIMax,
    UnivLevelSucc,
    UnivLevelZero,
)
from poussins.errors import KernelTypeError
from poussins.kernel.proof_state import MetaVar
from poussins.kernel.equality import is_alpha_eq, is_def_eq
from poussins.kernel.eval import instantiate, instantiate_metavar, whnf
from poussins.kernel.typecheck import check_type, infer_type
from poussins.kernel.unification import unify
from poussins.kernel.univ import is_universe_leq


def _prop() -> ESort:
    return ESort(UnivLevelZero())


def _type1() -> ESort:
    return ESort(UnivLevelSucc(UnivLevelZero()))


def test_instantiate_metavar_replaces_assigned_metavars() -> None:
    expr = EApp(EMetaVar("g1"), EMetaVar("g2"))
    metavars = {
        "g1": MetaVar(statement=_prop(), assignment=EConst("f", ())),
        "g2": MetaVar(statement=_prop()),
    }

    result = instantiate_metavar(expr, metavars)

    assert result == EApp(EConst("f", ()), EMetaVar("g2"))


def test_whnf_beta_reduces_lambda_application() -> None:
    expr = EApp(ELam("x", _prop(), EVar("x")), EConst("True", ()))

    result = whnf(expr, {})

    assert result == EConst("True", ())


def test_infer_type_for_sort_returns_next_universe() -> None:
    inferred = infer_type(_prop(), context={}, metavars={})
    assert inferred == _type1()


def test_infer_type_var_unknown_raises() -> None:
    with pytest.raises(KernelTypeError):
        infer_type(EVar("x"), context={}, metavars={})


def test_infer_type_lambda_identity_returns_pi() -> None:
    expr = ELam("x", _prop(), EVar("x"))

    inferred = infer_type(expr, context={}, metavars={})

    assert inferred == EPi("x", _prop(), _prop())


def test_infer_type_pi_returns_imax_sort() -> None:
    expr = EPi("x", _prop(), _prop())

    inferred = infer_type(expr, context={}, metavars={})

    assert inferred == ESort(UnivLevelIMax(UnivLevelSucc(UnivLevelZero()), UnivLevelSucc(UnivLevelZero())))


def test_infer_type_app_argument_mismatch_raises() -> None:
    fn = ELam("x", _prop(), EVar("x"))
    arg = _prop()

    with pytest.raises(KernelTypeError):
        infer_type(EApp(fn, arg), context={}, metavars={})


def test_infer_type_lambda_body_must_have_type() -> None:
    expr = ELam("x", _prop(), EApp(EConst("bad", ()), EConst("bad", ())))

    with pytest.raises(KernelTypeError):
        infer_type(expr, context={}, metavars={})


def test_infer_type_pi_domain_must_be_sort() -> None:
    expr = EPi("x", EVar("x"), _prop())

    with pytest.raises(KernelTypeError):
        infer_type(expr, context={}, metavars={})


def test_infer_type_app_requires_function_type() -> None:
    expr = EApp(EConst("True", ()), EConst("True", ()))

    with pytest.raises(KernelTypeError):
        infer_type(expr, context={}, metavars={})


def test_infer_type_app_accepts_alpha_equivalent_argument_types() -> None:
    fn = ELam("f", EPi("y", _prop(), _prop()), EVar("f"))
    arg = ELam("z", _prop(), EVar("z"))

    inferred = infer_type(EApp(fn, arg), context={}, metavars={})

    assert inferred == EPi("y", _prop(), _prop())


def test_check_type_accepts_alpha_equivalent_argument_types() -> None:
    fn = ELam("f", EPi("y", _prop(), _prop()), EVar("f"))
    arg = ELam("z", _prop(), EVar("z"))

    assert check_type(EApp(fn, arg), EPi("y", _prop(), _prop()), context={}, metavars={})


def test_check_type_returns_true_when_types_match() -> None:
    expr = ELam("x", _prop(), EVar("x"))
    expected = EPi("x", _prop(), _prop())

    assert check_type(expr, expected, context={}, metavars={})


def test_check_type_returns_false_on_kernel_error() -> None:
    assert not check_type(EVar("x"), _prop(), context={}, metavars={})


def test_check_type_accepts_cumulative_universe_sort() -> None:
    assert check_type(_prop(), _type1(), context={}, metavars={})


def test_is_alpha_eq_handles_renamed_binders() -> None:
    t1 = ELam("x", _prop(), EVar("x"))
    t2 = ELam("y", _prop(), EVar("y"))

    assert is_alpha_eq(t1, t2)


def test_is_def_eq_handles_beta_equivalence() -> None:
    left = EApp(ELam("x", _prop(), EVar("x")), EConst("True", ()))
    right = EConst("True", ())

    assert is_def_eq(left, right, context={}, metavars={})


def test_instantiate_fully_resolves_chained_metavars() -> None:
    expr = EMetaVar("g1")
    metavars = {
        "g1": MetaVar(statement=_prop(), assignment=EMetaVar("g2")),
        "g2": MetaVar(statement=_prop(), assignment=EConst("True", ())),
    }

    assert instantiate(expr, metavars) == EConst("True", ())


def test_unify_assigns_unassigned_metavar() -> None:
    metavars = {"g": MetaVar(statement=_prop())}

    unified = unify(EMetaVar("g"), EConst("True", ()), context={}, metavars=metavars)

    assert unified["g"].assignment == EConst("True", ())


def test_unify_structural_mismatch_raises() -> None:
    with pytest.raises(KernelTypeError):
        unify(EConst("a", ()), EConst("b", ()), context={}, metavars={})


def test_unify_pi_with_distinct_binders_succeeds() -> None:
    t1 = EPi("x", _prop(), EVar("x"))
    t2 = EPi("y", _prop(), EVar("y"))

    unified = unify(t1, t2, context={}, metavars={})
    assert unified == {}


def test_is_universe_leq_covers_imax_branches() -> None:
    assert is_universe_leq(UnivLevelZero(), UnivLevelIMax(UnivLevelZero(), UnivLevelSucc(UnivLevelZero())))
    assert is_universe_leq(UnivLevelSucc(UnivLevelZero()), UnivLevelIMax(UnivLevelZero(), UnivLevelSucc(UnivLevelZero())))
    assert not is_universe_leq(UnivLevelIMax(UnivLevelZero(), UnivLevelSucc(UnivLevelZero())), UnivLevelZero())


def test_infer_type_match_returns_motive_applied_to_discriminee() -> None:
    expr = EMatch("Nat", EConst("zero", ()), ELam("x", _prop(), EVar("x")), ())

    assert infer_type(expr, context={}, metavars={}) == EApp(ELam("x", _prop(), EVar("x")), EConst("zero", ()))


def test_infer_type_unknown_expression_raises_not_implemented() -> None:
    class FakeExpr(Expr):
        pass

    with pytest.raises(NotImplementedError):
        infer_type(FakeExpr(), context={}, metavars={})


def test_is_alpha_eq_detects_bound_var_mismatch() -> None:
    assert not is_alpha_eq(EVar("x"), EVar("y"), bvars1=["x"], bvars2=[])
    assert is_alpha_eq(EVar("x"), EVar("y"), bvars1=["x"], bvars2=["y"])


def test_is_alpha_eq_detects_match_branch_length_mismatch() -> None:
    left = EMatch("Nat", EConst("n", ()), EConst("motive", ()), (EConst("zero", ()),))
    right = EMatch("Nat", EConst("n", ()), EConst("motive", ()), (EConst("zero", ()), EConst("succ", ())))

    assert not is_alpha_eq(left, right)


def test_is_def_eq_rejects_invalid_eta_expansion() -> None:
    expr = ELam("x", _prop(), EApp(EVar("x"), EVar("x")))

    assert not is_def_eq(expr, EVar("f"), context={}, metavars={})


def test_is_def_eq_matches_match_expressions() -> None:
    left = EMatch("Nat", EConst("n", ()), EConst("motive", ()), (EConst("zero", ()),))
    right = EMatch("Nat", EConst("n", ()), EConst("motive", ()), (EConst("zero", ()),))

    assert is_def_eq(left, right, context={}, metavars={})


def test_unify_reduces_whnf_to_alpha_equal_terms() -> None:
    expr = EApp(ELam("x", _prop(), EVar("x")), EConst("True", ()))

    assert unify(expr, EConst("True", ()), context={}, metavars={}) == {}


def test_unify_type_mismatch_raises() -> None:
    with pytest.raises(KernelTypeError):
        unify(EConst("a", ()), _prop(), context={}, metavars={})


def test_unify_match_inductive_mismatch_raises() -> None:
    left = EMatch("Nat", EConst("n", ()), EConst("motive", ()), ())
    right = EMatch("List", EConst("n", ()), EConst("motive", ()), ())

    with pytest.raises(KernelTypeError):
        unify(left, right, context={}, metavars={})


def test_unify_match_branch_length_mismatch_raises() -> None:
    left = EMatch("Nat", EConst("n", ()), EConst("motive", ()), (EConst("zero", ()),))
    right = EMatch("Nat", EConst("n", ()), EConst("motive", ()), (EConst("zero", ()), EConst("succ", ())))

    with pytest.raises(KernelTypeError):
        unify(left, right, context={}, metavars={})


def test_infer_type_pi_domain_must_be_sort_when_domain_is_non_sort_expr() -> None:
    expr = EPi("x", EVar("x"), _prop())
    context = {"x": EConst("bad", ())}

    with pytest.raises(KernelTypeError):
        infer_type(expr, context=context, metavars={})


def test_infer_type_lambda_body_must_be_sort_when_body_type_is_non_sort() -> None:
    expr = ELam("x", _prop(), EVar("y"))
    context = {"y": EConst("bad", ())}

    with pytest.raises(KernelTypeError):
        infer_type(expr, context=context, metavars={})


def test_infer_type_app_requires_function_type_when_fn_is_not_pi() -> None:
    expr = EApp(EConst("f", ()), EConst("arg", ()))
    context = {"f": EConst("A", ()), "arg": EConst("B", ())}

    with pytest.raises(KernelTypeError):
        infer_type(expr, context=context, metavars={})


def test_check_type_uses_universe_ordering_for_sort_comparison() -> None:
    assert check_type(EConst("x", ()), _type1(), context={"x": _prop()}, metavars={})


def test_is_alpha_eq_handles_meta_and_app_cases() -> None:
    assert is_alpha_eq(EMetaVar("g"), EMetaVar("g"))
    assert not is_alpha_eq(EApp(EConst("f", ()), EConst("x", ())), EApp(EConst("g", ()), EConst("x", ())))
    assert not is_alpha_eq(EConst("a", ()), EVar("a"))


def test_is_def_eq_rejects_invalid_eta_cases() -> None:
    body_not_app = ELam("x", _prop(), EVar("x"))
    arg_not_var = ELam("x", _prop(), EApp(EConst("f", ()), EConst("x", ())))
    arg_name_mismatch = ELam("x", _prop(), EApp(EVar("f"), EVar("y")))
    free_var_in_head = ELam("x", _prop(), EApp(EVar("x"), EVar("x")))

    assert not is_def_eq(body_not_app, EVar("f"), context={}, metavars={})
    assert not is_def_eq(arg_not_var, EVar("f"), context={}, metavars={})
    assert not is_def_eq(arg_name_mismatch, EVar("f"), context={}, metavars={})
    assert not is_def_eq(free_var_in_head, EVar("f"), context={}, metavars={})


def test_is_def_eq_rejects_invalid_reverse_eta_cases() -> None:
    body_not_app = ELam("x", _prop(), EVar("x"))
    arg_not_var = ELam("x", _prop(), EApp(EConst("f", ()), EConst("x", ())))
    arg_name_mismatch = ELam("x", _prop(), EApp(EVar("f"), EVar("y")))
    free_var_in_head = ELam("x", _prop(), EApp(EVar("x"), EVar("x")))

    assert not is_def_eq(EVar("f"), body_not_app, context={}, metavars={})
    assert not is_def_eq(EVar("f"), arg_not_var, context={}, metavars={})
    assert not is_def_eq(EVar("f"), arg_name_mismatch, context={}, metavars={})
    assert not is_def_eq(EVar("f"), free_var_in_head, context={}, metavars={})


def test_is_def_eq_handles_app_pi_and_match_structures() -> None:
    assert is_def_eq(EApp(EConst("f", ()), EConst("x", ())), EApp(EConst("f", ()), EConst("x", ())), context={}, metavars={})
    assert is_def_eq(EPi("x", _prop(), EConst("P", ())), EPi("y", _prop(), EConst("P", ())), context={}, metavars={})

    match_expr = EMatch("Nat", EConst("n", ()), EConst("motive", ()), (EConst("zero", ()),))
    assert is_def_eq(match_expr, match_expr, context={}, metavars={})


def test_unify_assigns_metavar_from_right_hand_side() -> None:
    metavars = {"g": MetaVar(statement=_prop())}

    unified = unify(EConst("True", ()), EMetaVar("g"), context={}, metavars=metavars)

    assert unified["g"].assignment == EConst("True", ())


def test_unify_reduces_metavariable_whnf_before_recursing() -> None:
    expr = EApp(ELam("x", _prop(), EMetaVar("g")), EConst("True", ()))
    metavars = {"g": MetaVar(statement=_prop())}

    unified = unify(expr, EConst("True", ()), context={}, metavars=metavars)

    assert unified["g"].assignment == EConst("True", ())


def test_unify_handles_match_expressions() -> None:
    left = EMatch("Nat", EConst("n", ()), EConst("motive", ()), (EConst("zero", ()),))
    right = EMatch("Nat", EConst("n", ()), EConst("motive", ()), (EConst("zero", ()),))

    assert unify(left, right, context={}, metavars={}) == {}


def test_whnf_leaves_non_lambda_applications_unchanged() -> None:
    expr = EApp(EConst("f", ()), EConst("x", ()))

    assert whnf(expr, {}) == expr


def test_infer_type_unknown_metavar_raises() -> None:
    with pytest.raises(KernelTypeError):
        infer_type(EMetaVar("g"), context={}, metavars={})


def test_infer_type_pi_body_must_be_sort() -> None:
    expr = EPi("x", _prop(), EVar("x"))

    assert infer_type(expr, context={}, metavars={}) == ESort(UnivLevelIMax(UnivLevelSucc(UnivLevelZero()), UnivLevelZero()))


def test_check_type_returns_false_for_non_sort_mismatch() -> None:
    assert not check_type(EConst("x", ()), EConst("y", ()), context={}, metavars={})


def test_is_alpha_eq_falls_back_to_false_for_unknown_nodes() -> None:
    class FakeExpr(Expr):
        pass

    assert not is_alpha_eq(FakeExpr(), FakeExpr())


def test_is_def_eq_rejects_mismatched_constructors() -> None:
    assert not is_def_eq(EConst("a", ()), EConst("b", ()), context={}, metavars={})


def test_is_def_eq_rejects_mismatched_app_types() -> None:
    assert not is_def_eq(EApp(EConst("f", ()), EConst("x", ())), EApp(EConst("g", ()), EConst("x", ())), context={}, metavars={})


def test_unify_applications_recurse_through_function_and_argument() -> None:
    expr = EApp(EConst("f", ()), EConst("x", ()))
    expected = EApp(EConst("f", ()), EConst("x", ()))

    assert unify(expr, expected, context={}, metavars={}) == {}


def test_unify_pi_with_non_alpha_equivalent_bodies() -> None:
    left = EPi("x", _prop(), EVar("x"))
    right = EPi("y", _prop(), EVar("z"))

    with pytest.raises(KernelTypeError):
        unify(left, right, context={}, metavars={})


def test_unify_match_branch_loop_uses_branch_unification() -> None:
    left = EMatch("Nat", EConst("n", ()), EConst("motive", ()), (EConst("zero", ()),))
    right = EMatch("Nat", EConst("n", ()), EConst("motive", ()), (EConst("succ", ()),))

    with pytest.raises(KernelTypeError):
        unify(left, right, context={}, metavars={})


def test_is_universe_leq_recurses_through_succ_levels() -> None:
    assert is_universe_leq(
        UnivLevelSucc(UnivLevelSucc(UnivLevelZero())),
        UnivLevelSucc(UnivLevelSucc(UnivLevelSucc(UnivLevelZero()))),
    )


def test_infer_type_pi_body_non_sort_raises() -> None:
    expr = EPi("x", _prop(), EConst("x", ()))

    assert infer_type(expr, context={"x": EConst("bad", ())}, metavars={}) == ESort(UnivLevelIMax(UnivLevelSucc(UnivLevelZero()), UnivLevelZero()))


def test_infer_type_pi_body_non_sort_with_distinct_variable_name_raises() -> None:
    expr = EPi("x", _prop(), EConst("y", ()))

    with pytest.raises(KernelTypeError):
        infer_type(expr, context={"y": EConst("bad", ())}, metavars={})


def test_check_type_reaches_false_path_for_non_sort_mismatch() -> None:
    assert not check_type(EConst("x", ()), EConst("y", ()), context={"x": EConst("A", ())}, metavars={})


def test_is_alpha_eq_returns_false_for_binder_domain_mismatch() -> None:
    left = EPi("x", EConst("A", ()), EVar("x"))
    right = EPi("y", EConst("B", ()), EVar("y"))

    assert not is_alpha_eq(left, right)


def test_is_def_eq_returns_false_for_mismatched_node_types() -> None:
    assert not is_def_eq(EConst("a", ()), ESort(UnivLevelZero()), context={}, metavars={})


def test_is_def_eq_reaches_pi_branch_with_binder_renaming() -> None:
    expr = EPi("x", EConst("A", ()), EConst("A", ()))
    other = EPi("y", EConst("A", ()), EConst("B", ()))

    assert not is_def_eq(expr, other, context={}, metavars={})


def test_is_def_eq_reaches_match_branch_with_inductive_mismatch() -> None:
    left = EMatch("Nat", EConst("n", ()), EConst("motive", ()), (EConst("zero", ()),))
    right = EMatch("List", EConst("n", ()), EConst("motive", ()), (EConst("zero", ()),))

    assert not is_def_eq(left, right, context={}, metavars={})


def test_is_def_eq_reaches_match_branch_with_discriminee_mismatch() -> None:
    left = EMatch("Nat", EConst("n", ()), EConst("motive", ()), (EConst("zero", ()),))
    right = EMatch("Nat", EConst("m", ()), EConst("motive", ()), (EConst("zero", ()),))

    assert not is_def_eq(left, right, context={}, metavars={})


def test_is_def_eq_reaches_match_branch_with_motive_mismatch() -> None:
    left = EMatch("Nat", EConst("n", ()), EConst("motive", ()), (EConst("zero", ()),))
    right = EMatch("Nat", EConst("n", ()), EConst("other", ()), (EConst("zero", ()),))

    assert not is_def_eq(left, right, context={}, metavars={})


def test_is_def_eq_reaches_match_branch_with_branch_content_mismatch() -> None:
    left = EMatch("Nat", EConst("n", ()), EConst("motive", ()), (EConst("zero", ()),))
    right = EMatch("Nat", EConst("n", ()), EConst("motive", ()), (EConst("succ", ()),))

    assert not is_def_eq(left, right, context={}, metavars={})


def test_is_def_eq_reaches_match_branch_with_length_mismatch() -> None:
    left = EMatch("Nat", EConst("n", ()), EConst("motive", ()), (EConst("zero", ()),))
    right = EMatch("Nat", EConst("n", ()), EConst("motive", ()), (EConst("zero", ()), EConst("succ", ())))

    assert not is_def_eq(left, right, context={}, metavars={})


def test_is_def_eq_returns_false_when_pi_domains_are_not_definitionally_equal() -> None:
    left = EPi("x", EConst("A", ()), EConst("B", ()))
    right = EPi("x", EConst("C", ()), EConst("B", ()))

    assert not is_def_eq(left, right, context={}, metavars={})


def test_unify_reaches_app_recursion_with_metavariables() -> None:
    metavars = {"g": MetaVar(statement=_prop())}
    expr = EApp(EConst("f", ()), EMetaVar("g"))
    target = EApp(EConst("f", ()), EConst("x", ()))

    unified = unify(expr, target, context={}, metavars=metavars)

    assert unified["g"].assignment == EConst("x", ())


def test_unify_reaches_match_branch_assignment() -> None:
    metavars = {"g": MetaVar(statement=_prop())}
    left = EMatch("Nat", EConst("n", ()), EConst("motive", ()), (EMetaVar("g"),))
    right = EMatch("Nat", EConst("n", ()), EConst("motive", ()), (EConst("zero", ()),))

    unified = unify(left, right, context={}, metavars=metavars)

    assert unified["g"].assignment == EConst("zero", ())
