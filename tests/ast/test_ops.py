"""Test cases for AST operations in `poussins.ast`."""
import pytest

from poussins.ast import (
    EApp,
    EConst,
    EFVar,
    ELam,
    EMetaVar,
    EPi,
    ESort,
    UnivLevelZero,
    collect_free_vars,
    collect_metavar_ids,
    has_metavar,
    substitute_metavar,
    substitute_var,
)


def nat_cases_on(discriminee, motive, zero_case, succ_case):
    """Build `Nat.casesOn` application in core AST form."""
    return EApp(
        EApp(
            EApp(
                EApp(EConst("Nat.casesOn", ()), discriminee),
                motive,
            ),
            zero_case,
        ),
        succ_case,
    )


class TestHasMetaVar:
    """Test cases for `has_metavar`."""

    def test_positive_witnesses(self):
        """Predicate returns True when a metavariable occurs."""
        assert has_metavar(EMetaVar("m1"))
        assert has_metavar(EPi("x", EMetaVar("m1"), EFVar("x")))
        assert has_metavar(ELam("x", EFVar("A"), EMetaVar("m1")))
        assert has_metavar(EApp(EFVar("f"), EMetaVar("m1")))
        assert has_metavar(
            nat_cases_on(
                EMetaVar("m1"),
                EFVar("P"),
                EConst("z", ()),
                EConst("s", ()),
            )
        )

    def test_negative_witnesses(self):
        """Predicate returns False when no metavariable occurs."""
        assert not has_metavar(ESort(UnivLevelZero()))
        assert not has_metavar(EFVar("x"))
        assert not has_metavar(EConst("nat", ()))
        assert not has_metavar(EPi("x", EFVar("A"), EFVar("x")))
        assert not has_metavar(ELam("x", EFVar("A"), EFVar("x")))
        assert not has_metavar(EApp(EFVar("f"), EFVar("x")))
        assert not has_metavar(
            nat_cases_on(
                EFVar("n"),
                EFVar("P"),
                EConst("z", ()),
                EConst("s", ()),
            )
        )


class TestSubstituteMetaVar:
    """Test cases for `substitute_metavar`."""

    def test_replaces_target_occurrences(self):
        """Target metavariable occurrences are replaced structurally."""
        term = EConst("t", ())
        m = EMetaVar("m")

        assert substitute_metavar(m, m.goal_id, term) == term
        assert substitute_metavar(
            EPi("x", m, EFVar("x")), m.goal_id, term
        ) == EPi("x", term, EFVar("x"))
        assert substitute_metavar(
            ELam("x", EFVar("A"), m), m.goal_id, term
        ) == ELam("x", EFVar("A"), term)
        assert substitute_metavar(
            EApp(EFVar("f"), m), m.goal_id, term
        ) == EApp(EFVar("f"), term)
        assert substitute_metavar(
            nat_cases_on(m, EFVar("P"), EConst("z", ()), EConst("s", ())),
            m.goal_id,
            term,
        ) == nat_cases_on(term, EFVar("P"), EConst("z", ()), EConst("s", ()))

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
        assert substitute_metavar(EFVar("x"), m.goal_id, term) == EFVar("x")
        assert substitute_metavar(
            EConst("nat", ()), m.goal_id, term
        ) == EConst("nat", ())
        assert substitute_metavar(
            EPi("x", EFVar("A"), EFVar("x")), m.goal_id, term
        ) == EPi("x", EFVar("A"), EFVar("x"))
        assert substitute_metavar(
            ELam("x", EFVar("A"), EFVar("x")), m.goal_id, term
        ) == ELam("x", EFVar("A"), EFVar("x"))
        assert substitute_metavar(
            EApp(EFVar("f"), EFVar("x")), m.goal_id, term
        ) == EApp(EFVar("f"), EFVar("x"))
        assert substitute_metavar(
            nat_cases_on(EFVar("n"), EFVar("P"), EConst("z", ()), EConst("s", ())),
            m.goal_id,
            term,
        ) == nat_cases_on(EFVar("n"), EFVar("P"), EConst("z", ()), EConst("s", ()))

    def test_rejects_none_replacement(self):
        """Substitution rejects missing replacement witnesses."""
        with pytest.raises(ValueError):
            substitute_metavar(EMetaVar("m1"), "m1", None)


class TestSubstituteExprVar:
    """Test cases for `substitute_var`."""

    def test_replaces_target_occurrences(self):
        """Target variable occurrences are replaced structurally."""
        before = EFVar("x")
        after = EFVar("y")

        assert substitute_var(before, before.name, after) == after
        assert substitute_var(
            EApp(before, before), "x", after
        ) == EApp(after, after)
        assert substitute_var(
            EPi("x", before, EFVar("x")), "x", after
        ) == EPi("x", after, EFVar("x"))
        assert substitute_var(
            ELam("x", EFVar("x"), EFVar("x")), "x", after
        ) == ELam("x", after, EFVar("x"))
        assert substitute_var(
            nat_cases_on(EFVar("x"), EFVar("x"), EFVar("x"), EFVar("s")),
            "x",
            after,
        ) == nat_cases_on(after, after, after, EFVar("s"))

    def test_preserves_nontarget_variables(self):
        """Only the specified variable is replaced."""
        before = EFVar("x")
        after = EFVar("y")

        expr = EApp(before, EFVar("z"))
        expected = EApp(after, EFVar("z"))
        assert substitute_var(expr, "x", after) == expected

    def test_replaces_all_occurrences(self):
        """All occurrences of the target variable are replaced."""
        before = EFVar("x")
        after = EFVar("y")
        expr = EApp(before, before)
        expected = EApp(after, after)
        assert substitute_var(expr, "x", after) == expected

    def test_identity_when_target_absent(self):
        """Substitution is identity when target variable is absent."""
        after = EFVar("y")

        assert substitute_var(
            ESort(UnivLevelZero()), "x", after
        ) == ESort(UnivLevelZero())
        assert substitute_var(EConst("nat", ()), "x", after) == EConst("nat", ())
        assert substitute_var(EMetaVar("g1"), "x", after) == EMetaVar("g1")
        assert substitute_var(EFVar("y"), "x", after) == EFVar("y")
        assert substitute_var(
            EApp(EFVar("f"), EFVar("y")), "x", after
        ) == EApp(EFVar("f"), EFVar("y"))
        assert substitute_var(
            nat_cases_on(EFVar("n"), EFVar("P"), EConst("z", ()), EConst("s", ())),
            "x",
            after,
        ) == nat_cases_on(EFVar("n"), EFVar("P"), EConst("z", ()), EConst("s", ()))

    def test_capture_avoiding_renaming_for_pi(self):
        """Substitution alpha-renames Pi binders to avoid variable capture."""
        result = substitute_var(EPi("y", EFVar("x"), EFVar("x")), "x", EFVar("y"))
        assert result == EPi("y_", EFVar("y"), EFVar("y"))

    def test_capture_avoiding_renaming_for_lambda(self):
        """Substitution alpha-renames lambda binders to avoid variable capture."""
        result = substitute_var(ELam("y", EFVar("x"), EFVar("x")), "x", EFVar("y"))
        assert result == ELam("y_", EFVar("y"), EFVar("y"))

    def test_capture_renaming_with_collision_chain_for_pi(self):
        """Pi binder renaming keeps extending underscores until fresh."""
        replacement = EApp(EFVar("y"), EFVar("y_"))
        result = substitute_var(EPi("y", EFVar("x"), EFVar("x")), "x", replacement)
        assert result == EPi("y__", replacement, replacement)

    def test_capture_renaming_with_collision_chain_for_lambda(self):
        """Lambda binder renaming keeps extending underscores until fresh."""
        replacement = EApp(EFVar("y"), EFVar("y_"))
        result = substitute_var(
            ELam("y", EFVar("x"), EFVar("x")),
            "x",
            replacement,
        )
        assert result == ELam("y__", replacement, replacement)

    def test_non_capture_substitution_descends_under_pi_and_lambda(self):
        """Without capture risk, substitution proceeds under binders normally."""
        pi_result = substitute_var(EPi("y", EFVar("x"), EFVar("x")), "x", EFVar("z"))
        lam_result = substitute_var(
            ELam("y", EFVar("x"), EFVar("x")),
            "x",
            EFVar("z"),
        )
        assert pi_result == EPi("y", EFVar("z"), EFVar("z"))
        assert lam_result == ELam("y", EFVar("z"), EFVar("z"))


class TestCollectMetaVarIds:
    """Test cases for `collect_metavar_ids`."""

    def test_coverage_and_uniqueness(self):
        """Collector traverses syntax and deduplicates in encounter order."""
        # Cases where no metavariables are included (ESort, EFVar, EConst)
        assert collect_metavar_ids(ESort(UnivLevelZero())) == []
        assert collect_metavar_ids(EFVar("x")) == []
        assert collect_metavar_ids(EConst("nat", ())) == []

        # Cases with metavariables, multiple occurrences, and duplicates
        expr = EApp(EMetaVar("g1"), EApp(EMetaVar("g2"), EMetaVar("g1")))
        assert collect_metavar_ids(expr) == ["g1", "g2"]

        # Coverage for EPi / ELam / casesOn application
        pi_expr = EPi("x", EMetaVar("g3"), EMetaVar("g1"))
        assert collect_metavar_ids(pi_expr) == ["g3", "g1"]

        lam_expr = ELam("x", EMetaVar("g1"), EMetaVar("g4"))
        assert collect_metavar_ids(lam_expr) == ["g1", "g4"]

        match_expr = nat_cases_on(
            EMetaVar("g2"),
            EMetaVar("g1"),
            EMetaVar("g2"),
            EMetaVar("g5"),
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
        assert collect_free_vars(EFVar("x")) == {"x"}

        app_expr = EApp(EFVar("x"), EFVar("x"))
        assert collect_free_vars(app_expr) == {"x"}

        # Cases with binding and multiple free variables
        pi_expr = EPi("x", EFVar("A"), EApp(EFVar("x"), EFVar("B")))
        assert collect_free_vars(pi_expr) == {"A", "B"}

        lam_expr = ELam("x", EFVar("A"), EApp(EFVar("x"), EFVar("C")))
        assert collect_free_vars(lam_expr) == {"A", "C"}

        match_expr = nat_cases_on(EFVar("x"), EFVar("y"), EFVar("x"), EFVar("z"))
        assert collect_free_vars(match_expr) == {"x", "y", "z"}
