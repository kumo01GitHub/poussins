"""Mathematical soundness tests for `poussins.kernel.unification`."""
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
    UnivLevelParam,
    UnivLevelSucc,
    UnivLevelZero,
)
from poussins.environment import DefinitionDeclaration, Environment
from poussins.errors import KernelTypeError
from poussins.kernel.proof_state import MetaVar
from poussins.kernel.unification import unify


class TestUnificationAssignmentRules:
    """Assignment and occurs-check rules in first-order-style unification."""

    sort_prop: Final = ESort(UnivLevelZero())
    sort_type: Final = ESort(UnivLevelSucc(UnivLevelZero()))

    def test_assigns_open_metavar_on_left(self):
        """An open metavariable on the left is solved by the right term."""
        statement = EVar("A")
        metavars = {"m1": MetaVar(statement=statement)}
        result = unify(EMetaVar("m1"), EVar("x"), {}, metavars)
        assert result["m1"].assignment == EVar("x")

    def test_assigns_open_metavar_on_right(self):
        """An open metavariable on the right is solved by the left term."""
        statement = EVar("A")
        metavars = {"m1": MetaVar(statement=statement)}
        result = unify(EVar("x"), EMetaVar("m1"), {}, metavars)
        assert result["m1"].assignment == EVar("x")

    def test_rejects_assignment_to_unregistered_metavar(self):
        """Unregistered metavariables cannot be solved implicitly."""
        with pytest.raises(KernelTypeError, match=r"type mismatch"):
            unify(EMetaVar("m2"), EVar("x"), {}, {"m1": MetaVar(statement=EVar("A"))})

    def test_occurs_check_blocks_cyclic_solution(self):
        """Occurs-check rejects cyclic witnesses."""
        statement = EVar("A")
        metavars = {"m1": MetaVar(statement=statement)}
        with pytest.raises(KernelTypeError, match=r"occurs check failed"):
            unify(EMetaVar("m1"), EApp(EVar("f"), EMetaVar("m1")), {}, metavars)

    def test_assignment_propagates_through_application(self):
        """Function-part solving propagates to argument comparison."""
        statement = EVar("A")
        metavars = {"m1": MetaVar(statement=statement)}
        left = EApp(EMetaVar("m1"), EVar("x"))
        right = EApp(EVar("f"), EVar("x"))
        result = unify(left, right, {}, metavars)
        assert result["m1"].assignment == EVar("f")

    def test_lambda_unification_modulo_binder_names(self):
        """Lambda unification is stable under alpha-renaming."""
        left = ELam("x", self.sort_prop, EVar("x"))
        right = ELam("y", self.sort_prop, EVar("y"))
        result = unify(left, right, {}, {})
        assert result == {}

    def test_match_unification_when_components_agree(self):
        """Match expressions unify when all components unify."""
        left = EMatch("Nat", EVar("n"), EVar("P"), (EVar("z"), EVar("s")))
        right = EMatch("Nat", EVar("n"), EVar("P"), (EVar("z"), EVar("s")))
        result = unify(left, right, {}, {})
        assert result == {}

    def test_match_unification_fails_on_inductive_mismatch(self):
        """Different inductive families cannot unify."""
        left = EMatch("Nat", EVar("n"), EVar("P"), (EVar("z"),))
        right = EMatch("Bool", EVar("n"), EVar("P"), (EVar("z"),))
        with pytest.raises(KernelTypeError, match=r"inductive type mismatch"):
            unify(left, right, {}, {})

    def test_match_unification_fails_on_branch_arity(self):
        """Different branch arities cannot unify."""
        left = EMatch("Nat", EVar("n"), EVar("P"), (EVar("z"), EVar("s")))
        right = EMatch("Nat", EVar("n"), EVar("P"), (EVar("z"),))
        with pytest.raises(KernelTypeError, match=r"branch length mismatch"):
            unify(left, right, {}, {})

    def test_sort_unification_fails_on_universe_mismatch(self):
        """Unification fails when universe constraints are inconsistent."""
        with pytest.raises(KernelTypeError, match=r"universe level mismatch"):
            unify(self.sort_type, self.sort_prop, {}, {})

    def test_sort_unification_succeeds_with_universe_parameter(self):
        """Sort unification can solve through universe-level parameter unification."""
        result = unify(ESort(UnivLevelZero()), ESort(UnivLevelParam("u")), {}, {})
        assert result == {}

    def test_whnf_exposure_of_metavar_is_handled(self):
        """Unification proceeds after WHNF unfolding reveals a metavariable."""
        env = Environment()
        env.add(
            DefinitionDeclaration(
                name="k",
                level_params=(),
                type=self.sort_prop,
                value=EMetaVar("m1"),
            )
        )
        metavars = {"m1": MetaVar(statement=self.sort_prop)}
        result = unify(EConst("k", ()), EVar("x"), {}, metavars, env)
        assert result["m1"].assignment == EVar("x")

    def test_whnf_conversion_short_circuit(self):
        """If WHNF terms are alpha-equal, unification succeeds unchanged."""
        env = Environment()
        env.add(
            DefinitionDeclaration(
                name="id",
                level_params=(),
                type=self.sort_prop,
                value=ELam("x", self.sort_prop, EVar("x")),
            )
        )
        result = unify(EApp(EConst("id", ()), EVar("a")), EVar("a"), {}, {}, env)
        assert result == {}

    def test_pi_unification_with_binder_renaming_and_metavar_solution(self):
        """Pi/Lambda branch solves bodies after binder-name normalization."""
        metavars = {"m1": MetaVar(statement=self.sort_prop)}
        left = ELam("x", self.sort_prop, EMetaVar("m1"))
        right = ELam("y", self.sort_prop, EVar("y"))
        result = unify(left, right, {}, metavars)
        assert result["m1"].assignment == EVar("x")

    def test_match_unification_solves_branch_metavar(self):
        """Match unification traverses branches and solves metavariables."""
        metavars = {"m1": MetaVar(statement=self.sort_prop)}
        left = EMatch("Nat", EVar("n"), EVar("P"), (EMetaVar("m1"),))
        right = EMatch("Nat", EVar("n"), EVar("P"), (EVar("z"),))
        result = unify(left, right, {}, metavars)
        assert result["m1"].assignment == EVar("z")

    def test_pi_domain_mismatch_is_rejected(self):
        """Pi-types fail to unify when domains violate universe constraints."""
        left = EPi("x", self.sort_prop, EVar("x"))
        right = EPi("x", self.sort_type, EVar("x"))
        with pytest.raises(KernelTypeError, match=r"universe level mismatch"):
            unify(left, right, {}, {})

    def test_rejects_structurally_distinct_same_constructor(self):
        """Unification rejects unmatched structures with same top-level constructor."""
        with pytest.raises(KernelTypeError, match=r"structurally distinct"):
            unify(EVar("x"), EVar("y"), {}, {})

    def test_rejects_top_level_constructor_mismatch(self):
        """Unification rejects terms with different top-level constructors."""
        with pytest.raises(KernelTypeError, match=r"type mismatch"):
            unify(EVar("x"), EApp(EVar("f"), EVar("x")), {}, {})
