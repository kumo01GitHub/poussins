import pytest
from poussins.ast.universe import (
    UnivLevelZero,
    UnivLevelSucc,
    UnivLevelParam,
    UnivLevelMax,
    UnivLevelIMax,
)
from poussins.ast.expr import (
    Expr,
    ESort,
    EVar,
    EConst,
    EPi,
    ELam,
    EApp,
    EMatch,
    EMetaVar,
)
from poussins.kernel.univ import (
    is_universe_leq,
    unify_univ_levels,
    is_def_eq_univ,
    instantiate_univ_level,
    instantiate_univ,
)


# Unknown expression node for verifying NotImplementedError
class DummyExpr(Expr):
    pass


# ==========================================
# 1. Tests for is_universe_leq
# ==========================================
def test_is_universe_leq_success():
    zero = UnivLevelZero()
    succ_zero = UnivLevelSucc(zero)
    succ_succ_zero = UnivLevelSucc(succ_zero)
    param_u = UnivLevelParam("u")
    param_v = UnivLevelParam("v")
    max_uv = UnivLevelMax(param_u, param_v)
    imax_uv = UnivLevelIMax(param_u, succ_zero)

    # Reflexivity across all universe variants
    assert is_universe_leq(zero, zero) is True
    assert is_universe_leq(succ_zero, succ_zero) is True
    assert is_universe_leq(param_u, param_u) is True
    assert is_universe_leq(max_uv, max_uv) is True
    assert is_universe_leq(imax_uv, imax_uv) is True

    # Zero and Successor valid relations
    assert is_universe_leq(zero, succ_zero) is True
    assert is_universe_leq(zero, succ_succ_zero) is True
    assert is_universe_leq(succ_zero, succ_succ_zero) is True

    # IMax valid relations
    assert is_universe_leq(zero, imax_uv) is True
    assert is_universe_leq(succ_zero, imax_uv) is True

    # Invalid inequalities (Failure / False cases)
    assert is_universe_leq(succ_zero, zero) is False
    assert is_universe_leq(max_uv, zero) is False


# ==========================================
# 2. Tests for unify_univ_levels
# ==========================================
def test_unify_univ_levels_success():
    zero = UnivLevelZero()
    succ_zero = UnivLevelSucc(zero)
    param_u = UnivLevelParam("u")
    param_v = UnivLevelParam("v")
    max_uv = UnivLevelMax(param_u, param_v)
    imax_uv = UnivLevelIMax(param_u, param_v)

    # Identical levels
    assert unify_univ_levels(zero, zero, {}) == {}
    assert unify_univ_levels(max_uv, max_uv, {}) == {}

    # Parameter and successor unification
    assert unify_univ_levels(param_u, zero, {}) == {"u": zero}
    assert unify_univ_levels(succ_zero, param_u, {}) == {"u": succ_zero}
    assert unify_univ_levels(param_u, succ_zero, {"u": succ_zero}) == {"u": succ_zero}
    assert unify_univ_levels(UnivLevelSucc(param_u), UnivLevelSucc(zero), {}) == {"u": zero}

    # IMax unification
    imax1 = UnivLevelIMax(param_u, param_v)
    imax2 = UnivLevelIMax(zero, succ_zero)
    subst = unify_univ_levels(imax1, imax2, {})
    assert subst == {"u": zero, "v": succ_zero}


def test_unify_univ_levels_failure():
    zero = UnivLevelZero()
    succ_zero = UnivLevelSucc(zero)
    param_u = UnivLevelParam("u")
    param_v = UnivLevelParam("v")
    max_uv = UnivLevelMax(param_u, param_v)

    # Unification failures returning None (Failure cases)
    assert unify_univ_levels(succ_zero, zero, {}) is None
    assert unify_univ_levels(max_uv, zero, {}) is None


# ==========================================
# 3. Tests for is_def_eq_univ
# ==========================================
def test_is_def_eq_univ_success():
    zero = UnivLevelZero()
    succ_zero = UnivLevelSucc(zero)
    param_u = UnivLevelParam("u")
    max_uv = UnivLevelMax(param_u, zero)

    assert is_def_eq_univ(zero, zero) is True
    assert is_def_eq_univ(succ_zero, succ_zero) is True
    assert is_def_eq_univ(param_u, zero) is True
    assert is_def_eq_univ(max_uv, max_uv) is True
    assert is_def_eq_univ(succ_zero, zero) is False


# ==========================================
# 4. Tests for instantiate_univ_level
# ==========================================
def test_instantiate_univ_level_success():
    zero = UnivLevelZero()
    param_u = UnivLevelParam("u")
    param_v = UnivLevelParam("v")
    subst = {"u": zero}

    # Empty substitution check
    assert instantiate_univ_level(param_u, {}) == param_u

    # Individual universe level variants coverage (Success / substitution)
    assert instantiate_univ_level(param_u, subst) == zero
    assert instantiate_univ_level(zero, subst) == zero
    assert instantiate_univ_level(UnivLevelSucc(param_u), subst) == UnivLevelSucc(zero)
    assert instantiate_univ_level(UnivLevelIMax(param_u, param_v), subst) == UnivLevelIMax(zero, param_v)
    # Fallback / default case (e.g., UnivLevelMax falling into case _:)
    max_lvl = UnivLevelMax(param_u, param_v)
    assert instantiate_univ_level(max_lvl, subst) == max_lvl


# ==========================================
# 5. Tests for instantiate_univ
# ==========================================
def test_instantiate_univ_success():
    param_u = UnivLevelParam("u")
    zero = UnivLevelZero()
    subst = {"u": zero}

    # Empty substitution returns original expression
    var_expr = EVar("x")
    assert instantiate_univ(var_expr, {}) is var_expr

    # Individual Expr variants coverage (Success / substitution)
    assert instantiate_univ(EVar("x"), subst) == EVar("x")
    assert instantiate_univ(ESort(param_u), subst) == ESort(zero)
    assert instantiate_univ(EConst("nat", (param_u,)), subst) == EConst("nat", (zero,))
    assert instantiate_univ(EApp(EVar("f"), EConst("c", (param_u,))), subst) == EApp(EVar("f"), EConst("c", (zero,)))
    assert instantiate_univ(ELam("x", ESort(param_u), EVar("x")), subst) == ELam("x", ESort(zero), EVar("x"))
    assert instantiate_univ(EPi("x", ESort(param_u), EVar("x")), subst) == EPi("x", ESort(zero), EVar("x"))

    # Fallback variants returning as-is (EMatch, EMetaVar)
    match_expr = EMatch("Nat", EVar("n"), ESort(param_u), (EConst("z", (param_u,)),))
    assert instantiate_univ(match_expr, subst) == match_expr
    metavar_expr = EMetaVar("g1")
    assert instantiate_univ(metavar_expr, subst) == metavar_expr

def test_instantiate_univ_not_implemented():
    param_u = UnivLevelParam("u")
    zero = UnivLevelZero()
    subst = {"u": zero}

    dummy = DummyExpr()
    with pytest.raises(NotImplementedError):
        instantiate_univ(dummy, subst)
