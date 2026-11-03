"""Mathematical soundness tests for `poussins.kernel.eval`."""
from typing import Final

from poussins.ast import (
    EApp,
    EConst,
    EFVar,
    ELet,
    EMetaVar,
    ESort,
    UnivLevelZero,
    app,
    lam,
    let_,
)
from poussins.environment import DefinitionDeclaration
from poussins.framework import create_environment, create_standard_environment
from poussins.kernel.eval import instantiate, instantiate_metavar, whnf
from poussins.kernel.proof_state import MetaVar


class TestMetavarInstantiationSoundness:
    """Soundness of replacing solved metavariables."""

    statement: Final = ESort(UnivLevelZero())

    def test_replaces_assigned_metavar(self):
        """An assigned metavariable is definitionally replaced by its witness."""
        metavars = {
            "m1": MetaVar(statement=self.statement, assignment=EFVar("x")),
        }
        assert instantiate_metavar(EMetaVar("m1"), metavars) == EFVar("x")

    def test_preserves_unsolved_metavar(self):
        """An unsolved metavariable remains unchanged."""
        metavars = {
            "m1": MetaVar(statement=self.statement),
        }
        assert instantiate_metavar(EMetaVar("m1"), metavars) == EMetaVar("m1")


class TestRecursiveInstantiationClosure:
    """Closure under repeated substitution of metavariable assignments."""

    statement: Final = ESort(UnivLevelZero())

    def test_resolves_assignment_chain_to_normal_form(self):
        """Transitive assignments are normalized to a stable representative."""
        metavars = {
            "m1": MetaVar(statement=self.statement, assignment=EMetaVar("m2")),
            "m2": MetaVar(statement=self.statement, assignment=EFVar("x")),
        }
        assert instantiate(EMetaVar("m1"), metavars) == EFVar("x")


class TestWhnfConversionSoundness:
    """Soundness of weak-head reduction as a conversion relation."""

    sort_prop: Final = ESort(UnivLevelZero())

    def test_beta_reduction_at_head(self):
        """Head beta-redex reduces to substituted body."""
        expr = EApp(lam((("x", self.sort_prop),), "x"), EFVar("y"))
        assert whnf(expr, {}) == EFVar("y")

    def test_beta_reduction_keeps_shared_let_under_lambda(self):
        """Beta-reduction keeps a shared let when only lambda body needs binder."""
        expr = EApp(
            lam((("x", self.sort_prop), ("y", self.sort_prop)), "x"),
            EFVar("a"),
        )
        reduced = whnf(expr, {})
        assert isinstance(reduced, ELet)

    def test_application_continues_through_deferred_let(self):
        """Deferred let does not block subsequent head reduction."""
        expr = EApp(
            EApp(
                lam((("x", self.sort_prop), ("y", self.sort_prop)), "x"),
                EFVar("a"),
            ),
            EFVar("b"),
        )
        assert whnf(expr, {}) == EFVar("a")

    def test_zeta_reduction_for_let(self):
        """Let-bindings reduce by zeta-substitution at weak head."""
        expr = let_("x", self.sort_prop, EFVar("y"), "x")
        assert whnf(expr, {}) == EFVar("y")

    def test_delta_then_beta_on_head_constant(self):
        """Definition unfolding (delta) composes with head beta-reduction."""
        env = create_environment()
        env.add(
            DefinitionDeclaration(
                name="id",
                level_params=(),
                type=lam((("A", self.sort_prop),), "A"),
                value=lam((("x", self.sort_prop),), "x"),
            )
        )
        expr = EApp(EConst("id", ()), EFVar("z"))
        assert whnf(expr, {}, env) == EFVar("z")

    def test_guarded_unfolding_prevents_nontermination(self):
        """Unfolding guard blocks infinite delta-expansion on recursive heads."""
        env = create_environment()
        env.add(
            DefinitionDeclaration(
                name="loop",
                level_params=(),
                type=self.sort_prop,
                value=EConst("loop", ()),
            )
        )
        assert whnf(EConst("loop", ()), {}, env) == EConst("loop", ())

    def test_cases_on_reduces_constructor_discriminee(self):
        """`casesOn` on a constructor discriminee reduces to the matching branch."""
        env = create_standard_environment()
        nat = EConst("Nat", ())
        motive = lam((("_n", nat),), nat)
        expr = app(
            EConst("Nat.casesOn", ()),
            EConst("Nat.zero", ()),
            motive,
            EConst("Nat.zero", ()),
            lam((("k", nat),), "k"),
        )
        assert whnf(expr, {}, env) == EConst("Nat.zero", ())

    def test_cases_on_reduces_and_substitutes_constructor_arguments(self):
        """`casesOn` branch lambdas are instantiated with constructor arguments."""
        env = create_standard_environment()
        nat = EConst("Nat", ())
        discriminee = EApp(EConst("Nat.succ", ()), EConst("Nat.zero", ()))
        motive = lam((("_n", nat),), nat)
        expr = app(
            EConst("Nat.casesOn", ()),
            discriminee,
            motive,
            EConst("Nat.zero", ()),
            lam((("k", nat),), "k"),
        )
        assert whnf(expr, {}, env) == EConst("Nat.zero", ())
