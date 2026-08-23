import pytest
from typing import Final

from poussins.ast import (
    UnivLevel, UnivLevelZero, UnivLevelSucc, UnivLevelParam, UnivLevelMax, UnivLevelIMax,
    Expr, ESort, EVar, EConst, EPi, ELam, EApp, EMatch, EMetaVar,
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


class TestIsUniverseLeq:
    """
    Test cases for `is_universe_leq`.
    """
    zero: Final[UnivLevel] = UnivLevelZero()
    one: Final[UnivLevel] = UnivLevelSucc(zero)
    two: Final[UnivLevel] = UnivLevelSucc(one)

    param_u = UnivLevelParam("u")
    param_u_plus = UnivLevelSucc(param_u)
    param_v = UnivLevelParam("v")
    max_uv = UnivLevelMax(param_u, param_v)
    imax_uv = UnivLevelIMax(param_u, param_v)

    def test_equal(self):
        assert is_universe_leq(self.zero, self.zero) is True
        assert is_universe_leq(self.one, self.one) is True
        assert is_universe_leq(self.two, self.two) is True

        assert is_universe_leq(self.param_u, self.param_u) is True
        assert is_universe_leq(self.max_uv, self.max_uv) is True
        assert is_universe_leq(self.imax_uv, self.imax_uv) is True

    def test_right_zero(self):
        assert is_universe_leq(self.zero, self.zero) is True
        assert is_universe_leq(self.one, self.zero) is False
        assert is_universe_leq(self.two, self.zero) is False

        assert is_universe_leq(self.param_u, self.zero) is False
        assert is_universe_leq(self.max_uv, self.zero) is False
        assert is_universe_leq(self.imax_uv, self.zero) is False


class TestUnifyUnivLevels:
    """
    Test cases for `unify_univ_levels`.
    """

    def test_unify_univ_levels_success(self):
        zero = UnivLevelZero()
        succ_zero = UnivLevelSucc(zero)
        param_u = UnivLevelParam("u")
        param_v = UnivLevelParam("v")
        max_uv = UnivLevelMax(param_u, param_v)

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

    def test_unify_univ_levels_failure(self):
        zero = UnivLevelZero()
        succ_zero = UnivLevelSucc(zero)
        param_u = UnivLevelParam("u")
        param_v = UnivLevelParam("v")
        max_uv = UnivLevelMax(param_u, param_v)

        # Unification failures returning None (Failure cases)
        assert unify_univ_levels(succ_zero, zero, {}) is None
        assert unify_univ_levels(max_uv, zero, {}) is None


class TestIsDefEqUniv:
    """
    Test cases for `is_def_eq_univ`.
    """

    def test_is_def_eq_univ_success(self):
        zero = UnivLevelZero()
        succ_zero = UnivLevelSucc(zero)
        param_u = UnivLevelParam("u")
        max_uv = UnivLevelMax(param_u, zero)

        assert is_def_eq_univ(zero, zero) is True
        assert is_def_eq_univ(succ_zero, succ_zero) is True
        assert is_def_eq_univ(param_u, zero) is True
        assert is_def_eq_univ(max_uv, max_uv) is True
        assert is_def_eq_univ(succ_zero, zero) is False

    def test_is_def_eq_univ_failure(self):
        zero = UnivLevelZero()
        succ_zero = UnivLevelSucc(zero)
        param_u = UnivLevelParam("u")
        param_v = UnivLevelParam("v")
        max_uv = UnivLevelMax(param_u, param_v)

        # Failure cases returning False
        assert is_def_eq_univ(succ_zero, zero) is False
        assert is_def_eq_univ(max_uv, zero) is False


class TestInstantiateUnivLevel:
    """
    Test cases for `instantiate_univ_level`.
    """

    def test_instantiate_univ_level_success(self):
        param_u = UnivLevelParam("u")
        param_v = UnivLevelParam("v")
        zero = UnivLevelZero()
        one = UnivLevelSucc(zero)
        subst = {"u": zero, "v": one}

        # Individual UnivLevel variants coverage (Success / substitution)
        assert instantiate_univ_level(param_u, subst) == zero
        assert instantiate_univ_level(param_v, subst) == one
        assert instantiate_univ_level(UnivLevelSucc(param_u), subst) == UnivLevelSucc(zero)
        assert instantiate_univ_level(UnivLevelMax(param_u, param_v), subst) == UnivLevelMax(zero, one)
        assert instantiate_univ_level(UnivLevelIMax(param_u, param_v), subst) == UnivLevelIMax(zero, one)


class TestInstantiateUniv:
    """
    Test cases for `instantiate_univ`.
    """

    def test_instantiate_univ_success(self):
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

    def test_instantiate_univ_not_implemented(self):
        zero = UnivLevelZero()
        subst = {"u": zero}

        dummy = DummyExpr()
        with pytest.raises(NotImplementedError):
            instantiate_univ(dummy, subst)
