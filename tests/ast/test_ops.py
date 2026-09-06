"""Test cases for AST operations in `poussins.ast`."""
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
    UnivLevelZero,
    collect_free_vars,
    collect_metavar_ids,
    has_metavar,
    substitute_expr_var,
    substitute_metavar,
)


class TestHasMetaVar:
    """Test cases for `has_metavar`."""

    def test_positive_witnesses(self):
        """Predicate returns True when a metavariable occurs."""
        assert has_metavar(EMetaVar("m1"))
        assert has_metavar(EPi("x", EMetaVar("m1"), EVar("x")))
        assert has_metavar(ELam("x", EVar("A"), EMetaVar("m1")))
        assert has_metavar(EApp(EVar("f"), EMetaVar("m1")))
        assert has_metavar(EMatch("Nat", EMetaVar("m1"), EVar("P"), (EConst("z", ()),)))

    def test_negative_witnesses(self):
        """Predicate returns False when no metavariable occurs."""
        assert not has_metavar(ESort(UnivLevelZero()))
        assert not has_metavar(EVar("x"))
        assert not has_metavar(EConst("nat", ()))
        assert not has_metavar(EPi("x", EVar("A"), EVar("x")))
        assert not has_metavar(ELam("x", EVar("A"), EVar("x")))
        assert not has_metavar(EApp(EVar("f"), EVar("x")))
        assert not has_metavar(EMatch("Nat", EVar("n"), EVar("P"), (EConst("z", ()),)))


class TestSubstituteMetaVar:
    """Test cases for `substitute_metavar`."""

    def test_replaces_target_occurrences(self):
        """Target metavariable occurrences are replaced structurally."""
        term = EConst("t", ())
        m = EMetaVar("m")

        assert substitute_metavar(m, m.goal_id, term) == term
        assert substitute_metavar(
            EPi("x", m, EVar("x")), m.goal_id, term
        ) == EPi("x", term, EVar("x"))
        assert substitute_metavar(
            ELam("x", EVar("A"), m), m.goal_id, term
        ) == ELam("x", EVar("A"), term)
        assert substitute_metavar(
            EApp(EVar("f"), m), m.goal_id, term
        ) == EApp(EVar("f"), term)
        assert substitute_metavar(
            EMatch("Nat", m, EVar("P"), (EConst("z", ()),)), m.goal_id, term
        ) == EMatch("Nat", term, EVar("P"), (EConst("z", ()),))

    def test_preserves_nontarget_metavariables(self):
        """Only the specified metavariable is replaced."""
        term = EConst("t", ())
        m1 = EMetaVar("m1")
        m2 = EMetaVar("m2")

        expr = EApp(m1, m2)
        expected = EApp(term, m2)
        assert substitute_metavar(expr, m1.goal_id, term) == expected

    def test_replaces_all_occurrences(self):
        """All occurrences of the target metavariable are replaced."""
        term = EConst("t", ())
        m1 = EMetaVar("m1")
        expr = EApp(m1, m1)
        expected = EApp(term, term)
        assert substitute_metavar(expr, m1.goal_id, term) == expected

    def test_identity_when_target_absent(self):
        """Substitution is identity when target metavariable is absent."""
        term = EConst("t", ())
        m = EMetaVar("m")

        assert substitute_metavar(
            ESort(UnivLevelZero()), m.goal_id, term
        ) == ESort(UnivLevelZero())
        assert substitute_metavar(EVar("x"), m.goal_id, term) == EVar("x")
        assert substitute_metavar(
            EConst("nat", ()), m.goal_id, term
        ) == EConst("nat", ())
        assert substitute_metavar(
            EPi("x", EVar("A"), EVar("x")), m.goal_id, term
        ) == EPi("x", EVar("A"), EVar("x"))
        assert substitute_metavar(
            ELam("x", EVar("A"), EVar("x")), m.goal_id, term
        ) == ELam("x", EVar("A"), EVar("x"))
        assert substitute_metavar(
            EApp(EVar("f"), EVar("x")), m.goal_id, term
        ) == EApp(EVar("f"), EVar("x"))
        assert substitute_metavar(
            EMatch("Nat", EVar("n"), EVar("P"), (EConst("z", ()),)), m.goal_id, term
        ) == EMatch("Nat", EVar("n"), EVar("P"), (EConst("z", ()),))

    def test_rejects_none_replacement(self):
        """Substitution rejects missing replacement witnesses."""
        with pytest.raises(ValueError):
            substitute_metavar(EMetaVar("m1"), "m1", None)


class TestSubstituteExprVar:
    """Test cases for `substitute_expr_var`."""

    def test_replaces_target_occurrences(self):
        """Target variable occurrences are replaced structurally."""
        before = EVar("x")
        after = EVar("y")

        assert substitute_expr_var(before, before.name, after) == after
        assert substitute_expr_var(
            EApp(before, before), "x", after
        ) == EApp(after, after)
        assert substitute_expr_var(
            EPi("x", before, EVar("x")), "x", after
        ) == EPi("x", after, EVar("x"))
        assert substitute_expr_var(
            ELam("x", EVar("x"), EVar("x")), "x", after
        ) == ELam("x", after, EVar("x"))
        assert substitute_expr_var(
            EMatch("Nat", EVar("x"), EVar("x"), (EVar("x"),)), "x", after
        ) == EMatch("Nat", after, after, (after,))

    def test_preserves_nontarget_variables(self):
        """Only the specified variable is replaced."""
        before = EVar("x")
        after = EVar("y")

        expr = EApp(before, EVar("z"))
        expected = EApp(after, EVar("z"))
        assert substitute_expr_var(expr, "x", after) == expected

    def test_replaces_all_occurrences(self):
        """All occurrences of the target variable are replaced."""
        before = EVar("x")
        after = EVar("y")
        expr = EApp(before, before)
        expected = EApp(after, after)
        assert substitute_expr_var(expr, "x", after) == expected

    def test_identity_when_target_absent(self):
        """Substitution is identity when target variable is absent."""
        after = EVar("y")

        assert substitute_expr_var(
            ESort(UnivLevelZero()), "x", after
        ) == ESort(UnivLevelZero())
        assert substitute_expr_var(EConst("nat", ()), "x", after) == EConst("nat", ())
        assert substitute_expr_var(EMetaVar("g1"), "x", after) == EMetaVar("g1")
        assert substitute_expr_var(EVar("y"), "x", after) == EVar("y")
        assert substitute_expr_var(
            EApp(EVar("f"), EVar("y")), "x", after
        ) == EApp(EVar("f"), EVar("y"))
        assert substitute_expr_var(
            EMatch("Nat", EVar("n"), EVar("P"), (EConst("z", ()),)), "x", after
        ) == EMatch("Nat", EVar("n"), EVar("P"), (EConst("z", ()),))

    def test_capture_avoiding_renaming_for_pi(self):
        """Substitution alpha-renames Pi binders to avoid variable capture."""
        result = substitute_expr_var(EPi("y", EVar("x"), EVar("x")), "x", EVar("y"))
        assert result == EPi("y_", EVar("y"), EVar("y"))

    def test_capture_avoiding_renaming_for_lambda(self):
        """Substitution alpha-renames lambda binders to avoid variable capture."""
        result = substitute_expr_var(ELam("y", EVar("x"), EVar("x")), "x", EVar("y"))
        assert result == ELam("y_", EVar("y"), EVar("y"))

    def test_capture_renaming_with_collision_chain_for_pi(self):
        """Pi binder renaming keeps extending underscores until fresh."""
        replacement = EApp(EVar("y"), EVar("y_"))
        result = substitute_expr_var(EPi("y", EVar("x"), EVar("x")), "x", replacement)
        assert result == EPi("y__", replacement, replacement)

    def test_capture_renaming_with_collision_chain_for_lambda(self):
        """Lambda binder renaming keeps extending underscores until fresh."""
        replacement = EApp(EVar("y"), EVar("y_"))
        result = substitute_expr_var(
            ELam("y", EVar("x"), EVar("x")),
            "x",
            replacement,
        )
        assert result == ELam("y__", replacement, replacement)

    def test_non_capture_substitution_descends_under_pi_and_lambda(self):
        """Without capture risk, substitution proceeds under binders normally."""
        pi_result = substitute_expr_var(EPi("y", EVar("x"), EVar("x")), "x", EVar("z"))
        lam_result = substitute_expr_var(
            ELam("y", EVar("x"), EVar("x")),
            "x",
            EVar("z"),
        )
        assert pi_result == EPi("y", EVar("z"), EVar("z"))
        assert lam_result == ELam("y", EVar("z"), EVar("z"))


class TestCollectMetaVarIds:
    """Test cases for `collect_metavar_ids`."""

    def test_coverage_and_uniqueness(self):
        """Collector traverses syntax and deduplicates in encounter order."""
        # Cases where no metavariables are included (ESort, EVar, EConst)
        assert collect_metavar_ids(ESort(UnivLevelZero())) == []
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

        match_expr = EMatch(
            "Nat",
            EMetaVar("g2"),
            EMetaVar("g1"),
            (EMetaVar("g2"), EMetaVar("g5"))
        )
        assert collect_metavar_ids(match_expr) == ["g2", "g1", "g5"]


class TestCollectFreeVars:
    """Test cases for `collect_free_vars`."""

    def test_coverage_and_binding_exclusion(self):
        """Collector excludes bound variables and includes free occurrences."""
        # Cases where no free variables are included (ESort, EConst, EMetaVar)
        assert collect_free_vars(ESort(UnivLevelZero())) == set()
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
