"""Mathematical soundness tests for `poussins.kernel.unification`."""
from typing import Final

import pytest

from poussins.ast import (
    EApp,
    EBVar,
    EConst,
    EFVar,
    EMetaVar,
    ESort,
    UnivLevelParam,
    UnivLevelSucc,
    UnivLevelZero,
    lam,
    pi,
)
from poussins.environment import DefinitionDeclaration, Environment
from poussins.errors import KernelTypeError
from poussins.kernel.proof_state import MetaVar
from poussins.kernel.unification import unify


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


class TestUnificationAssignmentRules:
    """Assignment and occurs-check rules in first-order-style unification."""

    sort_prop: Final = ESort(UnivLevelZero())
    sort_type: Final = ESort(UnivLevelSucc(UnivLevelZero()))

    def test_assigns_open_metavar_on_left(self):
        """An open metavariable on the left is solved by the right term."""
        statement = EFVar("A")
        metavars = {"m1": MetaVar(statement=statement)}
        result = unify(EMetaVar("m1"), EFVar("x"), {}, metavars)
        assert result["m1"].assignment == EFVar("x")

    def test_assigns_open_metavar_on_right(self):
        """An open metavariable on the right is solved by the left term."""
        statement = EFVar("A")
        metavars = {"m1": MetaVar(statement=statement)}
        result = unify(EFVar("x"), EMetaVar("m1"), {}, metavars)
        assert result["m1"].assignment == EFVar("x")

    def test_rejects_assignment_to_unregistered_metavar(self):
        """Unregistered metavariables cannot be solved implicitly."""
        with pytest.raises(KernelTypeError, match=r"type mismatch"):
            unify(EMetaVar("m2"), EFVar("x"), {}, {"m1": MetaVar(statement=EFVar("A"))})

    def test_occurs_check_blocks_cyclic_solution(self):
        """Occurs-check rejects cyclic witnesses."""
        statement = EFVar("A")
        metavars = {"m1": MetaVar(statement=statement)}
        with pytest.raises(KernelTypeError, match=r"occurs check failed"):
            unify(EMetaVar("m1"), EApp(EFVar("f"), EMetaVar("m1")), {}, metavars)

    def test_assignment_propagates_through_application(self):
        """Function-part solving propagates to argument comparison."""
        statement = EFVar("A")
        metavars = {"m1": MetaVar(statement=statement)}
        left = EApp(EMetaVar("m1"), EFVar("x"))
        right = EApp(EFVar("f"), EFVar("x"))
        result = unify(left, right, {}, metavars)
        assert result["m1"].assignment == EFVar("f")

    def test_lambda_unification_modulo_binder_names(self):
        """Lambda unification is stable under alpha-renaming."""
        left = lam((("x", self.sort_prop),), "x")
        right = lam((("y", self.sort_prop),), "y")
        result = unify(left, right, {}, {})
        assert result == {}

    def test_cases_on_unification_when_components_agree(self):
        """`casesOn` expressions unify when all components unify."""
        left = nat_cases_on(EFVar("n"), EFVar("P"), EFVar("z"), EFVar("s"))
        right = nat_cases_on(EFVar("n"), EFVar("P"), EFVar("z"), EFVar("s"))
        result = unify(left, right, {}, {})
        assert result == {}

    def test_cases_on_unification_fails_on_head_mismatch(self):
        """Different eliminator constants cannot unify."""
        left = nat_cases_on(EFVar("n"), EFVar("P"), EFVar("z"), EFVar("s"))
        right = EApp(EConst("Bool.casesOn", ()), EFVar("n"))
        with pytest.raises(KernelTypeError, match=r"type mismatch"):
            unify(left, right, {}, {})

    def test_cases_on_unification_fails_on_arity(self):
        """Different argument arities cannot unify."""
        left = nat_cases_on(EFVar("n"), EFVar("P"), EFVar("z"), EFVar("s"))
        right = EApp(
            EApp(
                EApp(
                    EConst("Nat.casesOn", ()),
                    EFVar("n")
                ),
                EFVar("P")),
            EFVar("z")
        )
        with pytest.raises(KernelTypeError, match=r"type mismatch"):
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
        result = unify(EConst("k", ()), EFVar("x"), {}, metavars, env)
        assert result["m1"].assignment == EFVar("x")

    def test_whnf_conversion_short_circuit(self):
        """If WHNF terms are alpha-equal, unification succeeds unchanged."""
        env = Environment()
        env.add(
            DefinitionDeclaration(
                name="id",
                level_params=(),
                type=self.sort_prop,
                value=lam((("x", self.sort_prop),), "x"),
            )
        )
        result = unify(EApp(EConst("id", ()), EFVar("a")), EFVar("a"), {}, {}, env)
        assert result == {}

    def test_pi_unification_with_binder_renaming_and_metavar_solution(self):
        """Pi/Lambda branch solves bodies after binder-name normalization."""
        metavars = {"m1": MetaVar(statement=self.sort_prop)}
        left = lam((("x", self.sort_prop),), EMetaVar("m1"))
        right = lam((("y", self.sort_prop),), "y")
        result = unify(left, right, {}, metavars)
        assert result["m1"].assignment == EBVar(0)

    def test_cases_on_unification_solves_branch_metavar(self):
        """`casesOn` unification traverses branches and solves metavariables."""
        metavars = {"m1": MetaVar(statement=self.sort_prop)}
        left = nat_cases_on(EFVar("n"), EFVar("P"), EMetaVar("m1"), EFVar("s"))
        right = nat_cases_on(EFVar("n"), EFVar("P"), EFVar("z"), EFVar("s"))
        result = unify(left, right, {}, metavars)
        assert result["m1"].assignment == EFVar("z")

    def test_pi_domain_mismatch_is_rejected(self):
        """Pi-types fail to unify when domains violate universe constraints."""
        left = pi((("x", self.sort_prop),), "x")
        right = pi((("x", self.sort_type),), "x")
        with pytest.raises(KernelTypeError, match=r"universe level mismatch"):
            unify(left, right, {}, {})

    def test_rejects_structurally_distinct_same_constructor(self):
        """Unification rejects unmatched structures with same top-level constructor."""
        with pytest.raises(KernelTypeError, match=r"structurally distinct"):
            unify(EFVar("x"), EFVar("y"), {}, {})

    def test_rejects_top_level_constructor_mismatch(self):
        """Unification rejects terms with different top-level constructors."""
        with pytest.raises(KernelTypeError, match=r"type mismatch"):
            unify(EFVar("x"), EApp(EFVar("f"), EFVar("x")), {}, {})
