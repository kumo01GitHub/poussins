"""Mathematical soundness tests for `poussins.kernel.eval`."""
from typing import Final

from poussins.ast import (
    EApp,
    EConst,
    ELam,
    EMatch,
    EMetaVar,
    ESort,
    EVar,
    UnivLevelZero,
)
from poussins.environment import DefinitionDeclaration, Environment
from poussins.kernel.eval import instantiate, instantiate_metavar, whnf
from poussins.kernel.proof_state import MetaVar


class TestMetavarInstantiationSoundness:
    """Soundness of replacing solved metavariables."""

    statement: Final = ESort(UnivLevelZero())

    def test_replaces_assigned_metavar(self):
        """An assigned metavariable is definitionally replaced by its witness."""
        metavars = {
            "m1": MetaVar(statement=self.statement, assignment=EVar("x")),
        }
        assert instantiate_metavar(EMetaVar("m1"), metavars) == EVar("x")

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
            "m2": MetaVar(statement=self.statement, assignment=EVar("x")),
        }
        assert instantiate(EMetaVar("m1"), metavars) == EVar("x")


class TestWhnfConversionSoundness:
    """Soundness of weak-head reduction as a conversion relation."""

    sort_prop: Final = ESort(UnivLevelZero())

    def test_beta_reduction_at_head(self):
        """Head beta-redex reduces to substituted body."""
        expr = EApp(ELam("x", self.sort_prop, EVar("x")), EVar("y"))
        assert whnf(expr, {}) == EVar("y")

    def test_delta_then_beta_on_head_constant(self):
        """Definition unfolding (delta) composes with head beta-reduction."""
        env = Environment()
        env.add(
            DefinitionDeclaration(
                name="id",
                level_params=(),
                type=ELam("A", self.sort_prop, EVar("A")),
                value=ELam("x", self.sort_prop, EVar("x")),
            )
        )
        expr = EApp(EConst("id", ()), EVar("z"))
        assert whnf(expr, {}, env) == EVar("z")

    def test_guarded_unfolding_prevents_nontermination(self):
        """Unfolding guard blocks infinite delta-expansion on recursive heads."""
        env = Environment()
        env.add(
            DefinitionDeclaration(
                name="loop",
                level_params=(),
                type=self.sort_prop,
                value=EConst("loop", ()),
            )
        )
        assert whnf(EConst("loop", ()), {}, env) == EConst("loop", ())

    def test_match_reduces_constructor_discriminee(self):
        """Match on a constructor discriminee reduces to the matching branch."""
        env = Environment.standard()
        nat = EConst("Nat", ())
        motive = ELam("_n", nat, nat)
        expr = EMatch(
            "Nat",
            EConst("Nat.zero", ()),
            motive,
            (
                EConst("Nat.zero", ()),
                ELam("k", nat, EVar("k")),
            ),
        )
        assert whnf(expr, {}, env) == EConst("Nat.zero", ())

    def test_match_reduces_and_substitutes_constructor_arguments(self):
        """Match branch lambdas are instantiated with constructor arguments."""
        env = Environment.standard()
        nat = EConst("Nat", ())
        discriminee = EApp(EConst("Nat.succ", ()), EConst("Nat.zero", ()))
        motive = ELam("_n", nat, nat)
        expr = EMatch(
            "Nat",
            discriminee,
            motive,
            (
                EConst("Nat.zero", ()),
                ELam("k", nat, EVar("k")),
            ),
        )
        assert whnf(expr, {}, env) == EConst("Nat.zero", ())
