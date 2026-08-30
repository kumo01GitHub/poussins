from typing import Final

import pytest

from poussins.ast import (
    EApp,
    EConst,
    ELam,
    EMatch,
    EMetaVar,
    EPi,
    ESort,
    EVar,
    Expr,
    UnivLevel,
    UnivLevelIMax,
    UnivLevelMax,
    UnivLevelParam,
    UnivLevelSucc,
    UnivLevelZero,
)
from poussins.kernel.univ import (
    instantiate_univ,
    instantiate_univ_level,
    is_def_eq_univ,
    is_universe_leq,
    unify_univ_levels,
)


# Unknown expression node for verifying NotImplementedError
class DummyExpr(Expr):
    pass


class TestIsUniverseLeq:
    """Test cases for `is_universe_leq`."""

    zero: Final[UnivLevel] = UnivLevelZero()
    one: Final[UnivLevel] = UnivLevelSucc(zero)
    two: Final[UnivLevel] = UnivLevelSucc(one)

    param_u: Final[UnivLevel] = UnivLevelParam("u")
    param_v: Final[UnivLevel] = UnivLevelParam("v")
    max_uv: Final[UnivLevel] = UnivLevelMax(param_u, param_v)
    imax_uv: Final[UnivLevel] = UnivLevelIMax(param_u, param_v)

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
    """Test cases for `unify_univ_levels`."""

    zero: Final[UnivLevel] = UnivLevelZero()
    one: Final[UnivLevel] = UnivLevelSucc(zero)
    two: Final[UnivLevel] = UnivLevelSucc(one)

    param_u: Final[UnivLevel] = UnivLevelParam("u")
    param_v: Final[UnivLevel] = UnivLevelParam("v")
    max_uv: Final[UnivLevel] = UnivLevelMax(param_u, param_v)
    imax_uv: Final[UnivLevel] = UnivLevelIMax(param_u, param_v)

    def test_unify_univ_levels_success(self):
        # Identical levels
        assert unify_univ_levels(self.zero, self.zero, {}) == {}
        assert unify_univ_levels(self.max_uv, self.max_uv, {}) == {}

        # Parameter and successor unification
        assert unify_univ_levels(self.param_u, self.zero, {}) == {"u": self.zero}
        assert unify_univ_levels(self.one, self.param_u, {}) == {"u": self.one}
        assert unify_univ_levels(self.param_u, self.one, {"u": self.one}) == {"u": self.one}
        assert unify_univ_levels(UnivLevelSucc(self.param_u), self.one, {}) == {"u": self.zero}

        # IMax unification
        imax1 = UnivLevelIMax(self.param_u, self.param_v)
        imax2 = UnivLevelIMax(self.zero, self.one)
        subst = unify_univ_levels(imax1, imax2, {})
        assert subst == {"u": self.zero, "v": self.one}

    def test_unify_univ_levels_failure(self):
        # Unification failures returning None (Failure cases)
        assert unify_univ_levels(self.one, self.zero, {}) is None
        assert unify_univ_levels(self.max_uv, self.zero, {}) is None


class TestIsDefEqUniv:
    """Test cases for `is_def_eq_univ`."""

    zero: Final[UnivLevel] = UnivLevelZero()
    one: Final[UnivLevel] = UnivLevelSucc(zero)
    two: Final[UnivLevel] = UnivLevelSucc(one)

    param_u: Final[UnivLevel] = UnivLevelParam("u")
    param_v: Final[UnivLevel] = UnivLevelParam("v")
    max_uv: Final[UnivLevel] = UnivLevelMax(param_u, param_v)
    imax_uv: Final[UnivLevel] = UnivLevelIMax(param_u, param_v)

    def test_is_def_eq_univ_success(self):
        assert is_def_eq_univ(self.zero, self.zero) is True
        assert is_def_eq_univ(self.one, self.one) is True
        assert is_def_eq_univ(self.param_u, self.zero) is True
        assert is_def_eq_univ(self.max_uv, self.max_uv) is True
        assert is_def_eq_univ(self.one, self.zero) is False

    def test_is_def_eq_univ_failure(self):
        # Failure cases returning False
        assert is_def_eq_univ(self.one, self.zero) is False
        assert is_def_eq_univ(self.max_uv, self.zero) is False


class TestInstantiateUnivLevel:
    """Test cases for `instantiate_univ_level`.
    """

    param_u: Final[UnivLevel] = UnivLevelParam("u")
    param_v: Final[UnivLevel] = UnivLevelParam("v")
    zero: Final[UnivLevel] = UnivLevelZero()
    one: Final[UnivLevel] = UnivLevelSucc(zero)
    assignment: Final[dict[str, UnivLevel]] = {"u": zero, "v": one}

    def test_instantiate_univ_level_success(self):
        # Individual UnivLevel variants coverage (Success / substitution)
        assert instantiate_univ_level(self.param_u, self.assignment) == self.zero
        assert instantiate_univ_level(self.param_v, self.assignment) == self.one
        assert instantiate_univ_level(UnivLevelSucc(self.param_u), self.assignment) == self.one
        assert instantiate_univ_level(UnivLevelMax(self.param_u, self.param_v), self.assignment) == UnivLevelMax(self.zero, self.one)
        assert instantiate_univ_level(UnivLevelIMax(self.param_u, self.param_v), self.assignment) == UnivLevelIMax(self.zero, self.one)


class TestInstantiateUniv:
    """Test cases for `instantiate_univ`."""

    param_u: Final[UnivLevel] = UnivLevelParam("u")
    zero: Final[UnivLevel] = UnivLevelZero()
    assignment: Final[dict[str, UnivLevel]] = {"u": zero}

    def test_instantiate_univ_success(self):
        # Empty substitution returns original expression
        var_expr = EVar("x")
        assert instantiate_univ(var_expr, {}) is var_expr

        # Individual Expr variants coverage (Success / substitution)
        assert instantiate_univ(EVar("x"), self.assignment) == EVar("x")
        assert instantiate_univ(ESort(self.param_u), self.assignment) == ESort(self.zero)
        assert instantiate_univ(EConst("nat", (self.param_u,)), self.assignment) == EConst("nat", (self.zero,))
        assert instantiate_univ(EApp(EVar("f"), EConst("c", (self.param_u,))), self.assignment) == EApp(EVar("f"), EConst("c", (self.zero,)))
        assert instantiate_univ(ELam("x", ESort(self.param_u), EVar("x")), self.assignment) == ELam("x", ESort(self.zero), EVar("x"))
        assert instantiate_univ(EPi("x", ESort(self.param_u), EVar("x")), self.assignment) == EPi("x", ESort(self.zero), EVar("x"))

        # Fallback variants returning as-is (EMatch, EMetaVar)
        match_expr = EMatch("Nat", EVar("n"), ESort(self.param_u), (EConst("z", (self.param_u,)),))
        assert instantiate_univ(match_expr, self.assignment) == match_expr
        metavar_expr = EMetaVar("g1")
        assert instantiate_univ(metavar_expr, self.assignment) == metavar_expr

    def test_instantiate_univ_not_implemented(self):
        with pytest.raises(NotImplementedError):
            _ = instantiate_univ(DummyExpr(), self.assignment)
