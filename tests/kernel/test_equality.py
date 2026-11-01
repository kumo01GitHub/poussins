"""Mathematical soundness tests for `poussins.kernel.equality`."""
from typing import Final

from poussins.ast import (
    EApp,
    EBVar,
    EConst,
    EFVar,
    EMetaVar,
    ESort,
    UnivLevelParam,
    UnivLevelZero,
    lam,
    pi,
)
from poussins.environment import DefinitionDeclaration, Environment
from poussins.kernel.equality import is_alpha_eq, is_def_eq
from poussins.kernel.proof_state import MetaVar


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


class TestAlphaEquivalenceLaws:
    """Laws for alpha-equivalence (renaming of bound variables)."""

    sort_prop: Final = ESort(UnivLevelZero())

    def test_lambda_binder_renaming_invariant(self):
        """Lambda terms are equal modulo bound-variable renaming."""
        left = lam((("x", self.sort_prop),), "x")
        right = lam((("y", self.sort_prop),), "y")
        assert is_alpha_eq(left, right) is True

    def test_distinct_free_variables_not_equivalent(self):
        """Free-variable identity is preserved by alpha-equivalence."""
        assert is_alpha_eq(EFVar("x"), EFVar("y")) is False

    def test_bound_free_mismatch_not_equivalent(self):
        """A bound-variable occurrence is not equivalent to a free-variable one."""
        assert is_alpha_eq(EBVar(0), EFVar("x")) is False

    def test_sort_const_and_metavar_reflexivity(self):
        """Base constructors are alpha-equivalent under reflexive comparison."""
        assert is_alpha_eq(ESort(UnivLevelZero()), ESort(UnivLevelZero())) is True
        assert is_alpha_eq(EConst("c", ()), EConst("c", ())) is True
        left = nat_cases_on(EFVar("n"), EFVar("P"), EFVar("z"), EFVar("s"))
        right = nat_cases_on(EFVar("n"), EFVar("P"), EFVar("z"), EFVar("s"))
        assert is_alpha_eq(left, right) is True

    def test_metavar_reflexivity_and_mismatch(self):
        """Metavariables compare by goal id."""
        assert is_alpha_eq(EMetaVar("m1"), EMetaVar("m1")) is True
        assert is_alpha_eq(EMetaVar("m1"), EMetaVar("m2")) is False

    def test_rejects_unknown_expression_variant(self):
        """Unknown expression variants are conservatively treated as unequal."""
        class DummyExpr:
            pass

        dummy = DummyExpr()
        assert is_alpha_eq(dummy, dummy) is False  # type: ignore[arg-type]

    def test_cases_on_equivalence_is_structural(self):
        """`casesOn` terms are alpha-equal when components are pairwise equal."""
        left = nat_cases_on(EFVar("n"), EFVar("P"), EFVar("z"), EFVar("s"))
        right = nat_cases_on(EFVar("n"), EFVar("P"), EFVar("z"), EFVar("s"))
        assert is_alpha_eq(left, right) is True

    def test_cases_on_head_constant_must_agree(self):
        """Changing the head constant breaks alpha-equivalence."""
        left = nat_cases_on(EFVar("n"), EFVar("P"), EFVar("z"), EFVar("s"))
        right = EApp(EConst("Bool.casesOn", ()), EFVar("n"))
        assert is_alpha_eq(left, right) is False


class TestDefinitionalEqualityConversions:
    """Conversion rules for definitional equality."""

    sort_prop: Final = ESort(UnivLevelZero())
    sort_u: Final = ESort(UnivLevelParam("u"))
    statement: Final = ESort(UnivLevelZero())

    def test_beta_conversion(self):
        """Beta-convertible terms are definitionally equal."""
        left = EApp(lam((("x", self.sort_prop),), "x"), EFVar("a"))
        right = EFVar("a")
        assert is_def_eq(left, right, {}, {}) is True

    def test_delta_conversion(self):
        """Definition unfolding preserves definitional equality."""
        env = Environment()
        env.add(
            DefinitionDeclaration(
                name="id",
                level_params=(),
                type=lam((("A", self.sort_prop),), "A"),
                value=lam((("x", self.sort_prop),), "x"),
            )
        )
        left = EApp(EConst("id", ()), EFVar("a"))
        right = EFVar("a")
        assert is_def_eq(left, right, {}, {}, env) is True

    def test_eta_conversion(self):
        """Eta-convertible terms are definitionally equal."""
        left = lam((("x", self.sort_prop),), EApp(EFVar("f"), EFVar("x")))
        right = EFVar("f")
        assert is_def_eq(left, right, {}, {}) is True

    def test_eta_conversion_symmetric_direction(self):
        """Eta-convertibility is checked from variable-to-lambda direction too."""
        left = EFVar("f")
        right = lam((("x", self.sort_prop),), EApp(EFVar("f"), EFVar("x")))
        assert is_def_eq(left, right, {}, {}) is True

    def test_eta_symmetric_rejects_non_contractible_lambda(self):
        """Eta conversion rejects non-contractible terms in the symmetric case."""
        left = EFVar("x")
        right = lam((("x", self.sort_prop),), EApp(EFVar("x"), EFVar("x")))
        assert is_def_eq(left, right, {}, {}) is False

    def test_eta_conversion_rejects_when_variable_is_free_in_function(self):
        """Eta contraction is blocked when the binder is free in the function part."""
        left = lam((("x", self.sort_prop),), EApp(EFVar("x"), EFVar("x")))
        right = EFVar("x")
        assert is_def_eq(left, right, {}, {}) is False

    def test_eta_rejects_non_application_body(self):
        """Eta conversion requires lambda body to be an application."""
        left = lam((("x", self.sort_prop),), "x")
        assert is_def_eq(left, EFVar("x"), {}, {}) is False

    def test_eta_rejects_non_variable_argument(self):
        """Eta conversion requires the application argument to be a variable."""
        left = lam((("x", self.sort_prop),), EApp(EFVar("f"), ESort(UnivLevelZero())))
        assert is_def_eq(left, EFVar("f"), {}, {}) is False

    def test_eta_rejects_different_argument_name(self):
        """Eta conversion requires argument name to match binder name."""
        left = lam((("x", self.sort_prop),), EApp(EFVar("f"), EFVar("y")))
        assert is_def_eq(left, EFVar("f"), {}, {}) is False

    def test_conversion_after_metavar_instantiation(self):
        """Equality is checked after solving metavariables."""
        metavars = {
            "m1": MetaVar(statement=self.statement, assignment=EFVar("a")),
        }
        assert is_def_eq(EFVar("a"), EFVar("a"), {}, metavars) is True

    def test_nonconvertible_terms_are_rejected(self):
        """Structurally distinct non-convertible terms are not equal."""
        assert is_def_eq(EFVar("x"), EFVar("y"), {}, {}) is False

    def test_rejects_type_mismatch_between_whnfs(self):
        """Terms with different head constructors are not definitionally equal."""
        assert is_def_eq(EFVar("x"), ESort(UnivLevelZero()), {}, {}) is False

    def test_cases_on_defeq_requires_same_arity(self):
        """`casesOn` terms are not equal when argument arities differ."""
        left = nat_cases_on(EFVar("n"), EFVar("P"), EFVar("z"), EFVar("s"))
        right = EApp(EApp(EApp(EConst("Nat.casesOn", ()), EFVar("n")), EFVar("P")), EFVar("z"))
        assert is_def_eq(left, right, {}, {}) is False

    def test_cases_on_defeq_rejects_motive_mismatch(self):
        """`casesOn` terms require definitionally equal motives."""
        left = nat_cases_on(EFVar("n"), EFVar("P"), EFVar("z"), EFVar("s"))
        right = nat_cases_on(EFVar("n"), EFVar("Q"), EFVar("z"), EFVar("s"))
        assert is_def_eq(left, right, {}, {}) is False

    def test_cases_on_defeq_rejects_discriminee_mismatch(self):
        """`casesOn` terms require definitionally equal discriminees."""
        left = nat_cases_on(EFVar("n"), EFVar("P"), EFVar("z"), EFVar("s"))
        right = nat_cases_on(EFVar("m"), EFVar("P"), EFVar("z"), EFVar("s"))
        assert is_def_eq(left, right, {}, {}) is False

    def test_cases_on_defeq_rejects_head_mismatch(self):
        """`casesOn` terms require the same eliminator constant."""
        left = nat_cases_on(EFVar("n"), EFVar("P"), EFVar("z"), EFVar("s"))
        right = EApp(EConst("Bool.casesOn", ()), EFVar("n"))
        assert is_def_eq(left, right, {}, {}) is False

    def test_cases_on_defeq_accepts_convertible_branches(self):
        """`casesOn` equality checks argument convertibility recursively."""
        left = nat_cases_on(
            EFVar("n"),
            EFVar("P"),
            EApp(lam((("x", self.sort_prop),), "x"), EFVar("z")),
            EFVar("s"),
        )
        right = nat_cases_on(EFVar("n"), EFVar("P"), EFVar("z"), EFVar("s"))
        assert is_def_eq(left, right, {}, {}) is True

    def test_application_defeq_checks_function_and_argument(self):
        """Application equality checks both function and argument recursively."""
        left = EApp(
            EFVar("f"),
            EApp(lam((("x", self.sort_prop),), "x"), EFVar("a")),
        )
        right = EApp(EFVar("f"), EFVar("a"))
        assert is_def_eq(left, right, {}, {}) is True

    def test_pi_domain_mismatch_is_not_definitionally_equal(self):
        """Pi terms with non-convertible domains are not definitionally equal."""
        left = pi((("x", EFVar("A")),), "x")
        right = pi((("x", EFVar("B")),), "x")
        assert is_def_eq(left, right, {}, {}) is False

    def test_universe_level_conversion_for_sorts(self):
        """Sort equality delegates to universe-level definitional equality."""
        assert is_def_eq(self.sort_u, self.sort_prop, {}, {}) is True
