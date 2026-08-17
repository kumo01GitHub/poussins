import pytest
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
from poussins.ast.ops import (
    has_metavar,
    substitute_metavar,
    substitute_expr_var,
    collect_metavar_ids,
    collect_free_vars,
)


# Unknown expression node for verifying NotImplementedError
class DummyExpr(Expr):
    pass


# ==========================================
# 1. Tests for has_metavar
# ==========================================
def test_has_metavar_coverage_and_booleans():
    # Coverage for each Expr type (False cases)
    assert not has_metavar(ESort("Type"))
    assert not has_metavar(EVar("x"))
    assert not has_metavar(EConst("nat", ()))
    assert not has_metavar(EPi("x", EVar("A"), EVar("x")))
    assert not has_metavar(ELam("x", EVar("A"), EVar("x")))
    assert not has_metavar(EApp(EVar("f"), EVar("x")))
    assert not has_metavar(EMatch("Nat", EVar("n"), EVar("P"), (EConst("z", ()),)))

    # Coverage for each Expr type (True cases)
    assert has_metavar(EMetaVar("g1"))
    assert has_metavar(EPi("x", EMetaVar("g1"), EVar("x")))
    assert has_metavar(ELam("x", EVar("A"), EMetaVar("g1")))
    assert has_metavar(EApp(EVar("f"), EMetaVar("g1")))
    assert has_metavar(EMatch("Nat", EMetaVar("g1"), EVar("P"), (EConst("z", ()),)))


def test_has_metavar_not_implemented():
    with pytest.raises(NotImplementedError):
        has_metavar(DummyExpr())


# ==========================================
# 2. Tests for substitute_metavar
# ==========================================
def test_substitute_metavar_coverage_and_cases():
    replacement = EConst("c", ())

    # ESort, EVar, EConst, EMetaVar (not included / included / multiple)
    assert substitute_metavar(ESort("Type"), "g1", replacement) == ESort("Type")
    assert substitute_metavar(EVar("x"), "g1", replacement) == EVar("x")
    assert substitute_metavar(EConst("nat", ()), "g1", replacement) == EConst("nat", ())
    
    # EMetaVar: case where metavar is not included
    assert substitute_metavar(EMetaVar("g2"), "g1", replacement) == EMetaVar("g2")
    # EMetaVar: case where metavar is included
    assert substitute_metavar(EMetaVar("g1"), "g1", replacement) == replacement
    # EMetaVar: case with multiple occurrences
    multi_expr = EApp(EMetaVar("g1"), EMetaVar("g1"))
    assert substitute_metavar(multi_expr, "g1", replacement) == EApp(replacement, replacement)

    # EPi / ELam substitution
    pi_expr = EPi("x", EMetaVar("g1"), EMetaVar("g1"))
    assert substitute_metavar(pi_expr, "g1", replacement) == EPi("x", replacement, replacement)

    lam_expr = ELam("x", EMetaVar("g1"), EMetaVar("g1"))
    assert substitute_metavar(lam_expr, "g1", replacement) == ELam("x", replacement, replacement)

    # EMatch substitution
    match_expr = EMatch("Nat", EMetaVar("g1"), EMetaVar("g1"), (EMetaVar("g1"),))
    expected_match = EMatch("Nat", replacement, replacement, (replacement,))
    assert substitute_metavar(match_expr, "g1", replacement) == expected_match


def test_substitute_metavar_not_implemented():
    with pytest.raises(NotImplementedError):
        substitute_metavar(DummyExpr(), "g1", EConst("c", ()))


# ==========================================
# 3. Tests for substitute_expr_var
# ==========================================
def test_substitute_expr_var_coverage_and_cases():
    replacement = EVar("y")

    # ESort, EConst, EMetaVar
    assert substitute_expr_var(ESort("Type"), "x", replacement) == ESort("Type")
    assert substitute_expr_var(EConst("nat", ()), "x", replacement) == EConst("nat", ())
    assert substitute_expr_var(EMetaVar("g1"), "x", replacement) == EMetaVar("g1")

    # EVar: not included / included cases
    assert substitute_expr_var(EVar("z"), "x", replacement) == EVar("z")
    assert substitute_expr_var(EVar("x"), "x", replacement) == replacement

    # EApp: multiple occurrences case
    app_expr = EApp(EVar("x"), EVar("x"))
    assert substitute_expr_var(app_expr, "x", replacement) == EApp(replacement, replacement)

    # EPi: domain variable is substituted, bound body variable is shadowed
    pi_expr = EPi("x", EVar("x"), EVar("x"))
    expected_pi = EPi("x", replacement, EVar("x"))
    assert substitute_expr_var(pi_expr, "x", replacement) == expected_pi

    # ELam: domain variable is substituted, bound body variable is shadowed
    lam_expr = ELam("x", EVar("x"), EVar("x"))
    expected_lam = ELam("x", replacement, EVar("x"))
    assert substitute_expr_var(lam_expr, "x", replacement) == expected_lam

    # EMatch
    match_expr = EMatch("Nat", EVar("x"), EVar("x"), (EVar("x"),))
    expected_match = EMatch("Nat", replacement, replacement, (replacement,))
    assert substitute_expr_var(match_expr, "x", replacement) == expected_match


def test_substitute_expr_var_not_implemented():
    with pytest.raises(NotImplementedError):
        substitute_expr_var(DummyExpr(), "x", EVar("y"))


# ==========================================
# 4. Tests for collect_metavar_ids
# ==========================================
def test_collect_metavar_ids_coverage_and_cases():
    # Cases where no metavariables are included (ESort, EVar, EConst)
    assert collect_metavar_ids(ESort("Type")) == []
    assert collect_metavar_ids(EVar("x")) == []
    assert collect_metavar_ids(EConst("nat", ())) == []

    # Cases with metavariables, multiple occurrences, and duplicates
    expr = EApp(EMetaVar("g1"), EApp(EMetaVar("g2"), EMetaVar("g1")))
    assert collect_metavar_ids(expr) == ["g1", "g2"]

    # Coverage for EPi / ELam / EMatch
    pi_expr = EPi("x", EMetaVar("g3"), EMetaVar("g1"))
    assert collect_metavar_ids(pi_expr) == ["g3", "g1"]

    lam_expr = ELam("x", EMetaVar("g1"), EMetaVar("g4"))
    assert collect_metavar_ids(lam_expr) == ["g1", "g4"]

    match_expr = EMatch("Nat", EMetaVar("g2"), EMetaVar("g1"), (EMetaVar("g2"), EMetaVar("g5")))
    assert collect_metavar_ids(match_expr) == ["g2", "g1", "g5"]


def test_collect_metavar_ids_not_implemented():
    with pytest.raises(NotImplementedError):
        collect_metavar_ids(DummyExpr())


# ==========================================
# 5. Tests for collect_free_vars
# ==========================================
def test_collect_free_vars_coverage_and_cases():
    # Cases where no free variables are included (ESort, EConst, EMetaVar)
    assert collect_free_vars(ESort("Type")) == set()
    assert collect_free_vars(EConst("nat", ())) == set()
    assert collect_free_vars(EMetaVar("g1")) == set()

    # Cases with free variables, multiple occurrences, and duplicates
    assert collect_free_vars(EVar("x")) == {"x"}

    app_expr = EApp(EVar("x"), EVar("x"))
    assert collect_free_vars(app_expr) == {"x"}

    # Cases with binding and multiple free variables
    pi_expr = EPi("x", EVar("A"), EApp(EVar("x"), EVar("B")))
    assert collect_free_vars(pi_expr) == {"A", "B"}

    lam_expr = ELam("x", EVar("A"), EApp(EVar("x"), EVar("C")))
    assert collect_free_vars(lam_expr) == {"A", "C"}

    match_expr = EMatch("Nat", EVar("x"), EVar("y"), (EVar("x"), EVar("z")))
    assert collect_free_vars(match_expr) == {"x", "y", "z"}


def test_collect_free_vars_not_implemented():
    with pytest.raises(NotImplementedError):
        collect_free_vars(DummyExpr())
