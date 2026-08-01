import pytest

from poussins.ast import (
    EApp,
    EConst,
    ELam,
    EMetaVar,
    EPi,
    ESort,
    EVar,
    UnivLevelIMax,
    UnivLevelSucc,
    UnivLevelZero,
)
from poussins.errors import KernelTypeError
from poussins.kernel.proof_state import MetaVar
from poussins.kernel.typecheck import (
    check_type,
    infer_type,
    instantiate,
    instantiate_meta,
    is_alpha_eq,
    is_def_eq,
    unify,
    whnf,
)


def _prop() -> ESort:
    return ESort(UnivLevelZero())


def _type1() -> ESort:
    return ESort(UnivLevelSucc(UnivLevelZero()))


def test_instantiate_meta_replaces_assigned_metavars() -> None:
    expr = EApp(EMetaVar("g1"), EMetaVar("g2"))
    metavars = {
        "g1": MetaVar(statement=_prop(), assignment=EConst("f", ())),
        "g2": MetaVar(statement=_prop()),
    }

    result = instantiate_meta(expr, metavars)

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


def test_is_def_eq_handles_eta_equivalence() -> None:
    fn = EVar("f")
    eta_expanded = ELam("x", _prop(), EApp(EVar("f"), EVar("x")))
    context = {"f": EPi("x", _prop(), _prop())}

    assert is_def_eq(eta_expanded, fn, context=context, metavars={})


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
