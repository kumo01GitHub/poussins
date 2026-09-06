"""Mathematical soundness tests for `poussins.kernel.equality`."""
from typing import Final

from poussins.ast import (
    EApp,
    EConst,
    ELam,
    EMatch,
    EMetaVar,
    EPi,
    ESort,
    EVar,
    UnivLevelParam,
    UnivLevelZero,
)
from poussins.environment import DefinitionDeclaration, Environment
from poussins.kernel.equality import is_alpha_eq, is_def_eq
from poussins.kernel.proof_state import MetaVar


class TestAlphaEquivalenceLaws:
    """Laws for alpha-equivalence (renaming of bound variables)."""

    sort_prop: Final = ESort(UnivLevelZero())

    def test_lambda_binder_renaming_invariant(self):
        """Lambda terms are equal modulo bound-variable renaming."""
        left = ELam("x", self.sort_prop, EVar("x"))
        right = ELam("y", self.sort_prop, EVar("y"))
        assert is_alpha_eq(left, right) is True

    def test_distinct_free_variables_not_equivalent(self):
        """Free-variable identity is preserved by alpha-equivalence."""
        assert is_alpha_eq(EVar("x"), EVar("y")) is False

    def test_bound_free_mismatch_not_equivalent(self):
        """A bound-variable occurrence is not equivalent to a free-variable one."""
        assert is_alpha_eq(EVar("x"), EVar("y"), ["x"], []) is False

    def test_sort_const_and_metavar_reflexivity(self):
        """Base constructors are alpha-equivalent under reflexive comparison."""
        assert is_alpha_eq(ESort(UnivLevelZero()), ESort(UnivLevelZero())) is True
        assert is_alpha_eq(EConst("c", ()), EConst("c", ())) is True
        left = EMatch("N", EVar("n"), EVar("P"), ())
        right = EMatch("N", EVar("n"), EVar("P"), ())
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

    def test_match_equivalence_is_structural(self):
        """Match terms are alpha-equal when components are pairwise equal."""
        left = EMatch("Nat", EVar("n"), EVar("P"), (EVar("z"), EVar("s")))
        right = EMatch("Nat", EVar("n"), EVar("P"), (EVar("z"), EVar("s")))
        assert is_alpha_eq(left, right) is True

    def test_match_inductive_name_must_agree(self):
        """Changing the inductive family breaks alpha-equivalence."""
        left = EMatch("Nat", EVar("n"), EVar("P"), (EVar("z"),))
        right = EMatch("Bool", EVar("n"), EVar("P"), (EVar("z"),))
        assert is_alpha_eq(left, right) is False


class TestDefinitionalEqualityConversions:
    """Conversion rules for definitional equality."""

    sort_prop: Final = ESort(UnivLevelZero())
    sort_u: Final = ESort(UnivLevelParam("u"))
    statement: Final = ESort(UnivLevelZero())

    def test_beta_conversion(self):
        """Beta-convertible terms are definitionally equal."""
        left = EApp(ELam("x", self.sort_prop, EVar("x")), EVar("a"))
        right = EVar("a")
        assert is_def_eq(left, right, {}, {}) is True

    def test_delta_conversion(self):
        """Definition unfolding preserves definitional equality."""
        env = Environment()
        env.add(
            DefinitionDeclaration(
                name="id",
                level_params=(),
                type=ELam("A", self.sort_prop, EVar("A")),
                value=ELam("x", self.sort_prop, EVar("x")),
            )
        )
        left = EApp(EConst("id", ()), EVar("a"))
        right = EVar("a")
        assert is_def_eq(left, right, {}, {}, env) is True

    def test_eta_conversion(self):
        """Eta-convertible terms are definitionally equal."""
        left = ELam(
            "x",
            self.sort_prop,
            EApp(EVar("f"), EVar("x")),
        )
        right = EVar("f")
        assert is_def_eq(left, right, {}, {}) is True

    def test_eta_conversion_symmetric_direction(self):
        """Eta-convertibility is checked from variable-to-lambda direction too."""
        left = EVar("f")
        right = ELam("x", self.sort_prop, EApp(EVar("f"), EVar("x")))
        assert is_def_eq(left, right, {}, {}) is True

    def test_eta_symmetric_rejects_non_contractible_lambda(self):
        """Eta conversion rejects non-contractible terms in the symmetric case."""
        left = EVar("x")
        right = ELam("x", self.sort_prop, EApp(EVar("x"), EVar("x")))
        assert is_def_eq(left, right, {}, {}) is False

    def test_eta_conversion_rejects_when_variable_is_free_in_function(self):
        """Eta contraction is blocked when the binder is free in the function part."""
        left = ELam("x", self.sort_prop, EApp(EVar("x"), EVar("x")))
        right = EVar("x")
        assert is_def_eq(left, right, {}, {}) is False

    def test_eta_rejects_non_application_body(self):
        """Eta conversion requires lambda body to be an application."""
        left = ELam("x", self.sort_prop, EVar("x"))
        assert is_def_eq(left, EVar("x"), {}, {}) is False

    def test_eta_rejects_non_variable_argument(self):
        """Eta conversion requires the application argument to be a variable."""
        left = ELam("x", self.sort_prop, EApp(EVar("f"), ESort(UnivLevelZero())))
        assert is_def_eq(left, EVar("f"), {}, {}) is False

    def test_eta_rejects_different_argument_name(self):
        """Eta conversion requires argument name to match binder name."""
        left = ELam("x", self.sort_prop, EApp(EVar("f"), EVar("y")))
        assert is_def_eq(left, EVar("f"), {}, {}) is False

    def test_conversion_after_metavar_instantiation(self):
        """Equality is checked after solving metavariables."""
        metavars = {
            "m1": MetaVar(statement=self.statement, assignment=EVar("a")),
        }
        assert is_def_eq(EVar("a"), EVar("a"), {}, metavars) is True

    def test_nonconvertible_terms_are_rejected(self):
        """Structurally distinct non-convertible terms are not equal."""
        assert is_def_eq(EVar("x"), EVar("y"), {}, {}) is False

    def test_rejects_type_mismatch_between_whnfs(self):
        """Terms with different head constructors are not definitionally equal."""
        assert is_def_eq(EVar("x"), ESort(UnivLevelZero()), {}, {}) is False

    def test_match_defeq_requires_same_number_of_cases(self):
        """Match terms are not equal when branch arities differ."""
        left = EMatch("Nat", EVar("n"), EVar("P"), (EVar("z"), EVar("s")))
        right = EMatch("Nat", EVar("n"), EVar("P"), (EVar("z"),))
        assert is_def_eq(left, right, {}, {}) is False

    def test_match_defeq_rejects_motive_mismatch(self):
        """Match terms require definitionally equal motives."""
        left = EMatch("Nat", EVar("n"), EVar("P"), (EVar("z"),))
        right = EMatch("Nat", EVar("n"), EVar("Q"), (EVar("z"),))
        assert is_def_eq(left, right, {}, {}) is False

    def test_match_defeq_rejects_discriminee_mismatch(self):
        """Match terms require definitionally equal discriminees."""
        left = EMatch("Nat", EVar("n"), EVar("P"), (EVar("z"),))
        right = EMatch("Nat", EVar("m"), EVar("P"), (EVar("z"),))
        assert is_def_eq(left, right, {}, {}) is False

    def test_match_defeq_rejects_inductive_mismatch(self):
        """Match terms require the same inductive family."""
        left = EMatch("Nat", EVar("n"), EVar("P"), (EVar("z"),))
        right = EMatch("Bool", EVar("n"), EVar("P"), (EVar("z"),))
        assert is_def_eq(left, right, {}, {}) is False

    def test_match_defeq_accepts_convertible_branches(self):
        """Match equality checks branch convertibility recursively."""
        left = EMatch(
            "Nat",
            EVar("n"),
            EVar("P"),
            (EApp(ELam("x", self.sort_prop, EVar("x")), EVar("z")),),
        )
        right = EMatch("Nat", EVar("n"), EVar("P"), (EVar("z"),))
        assert is_def_eq(left, right, {}, {}) is True

    def test_application_defeq_checks_function_and_argument(self):
        """Application equality checks both function and argument recursively."""
        left = EApp(
            EVar("f"),
            EApp(ELam("x", self.sort_prop, EVar("x")), EVar("a")),
        )
        right = EApp(EVar("f"), EVar("a"))
        assert is_def_eq(left, right, {}, {}) is True

    def test_pi_domain_mismatch_is_not_definitionally_equal(self):
        """Pi terms with non-convertible domains are not definitionally equal."""
        left = EPi("x", EVar("A"), EVar("x"))
        right = EPi("x", EVar("B"), EVar("x"))
        assert is_def_eq(left, right, {}, {}) is False

    def test_universe_level_conversion_for_sorts(self):
        """Sort equality delegates to universe-level definitional equality."""
        assert is_def_eq(self.sort_u, self.sort_prop, {}, {}) is True
