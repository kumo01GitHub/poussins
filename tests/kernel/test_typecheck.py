"""Mathematical soundness tests for `poussins.kernel.typecheck`."""
from typing import Final

import pytest

from poussins.ast import (
    EApp,
    EBVar,
    EConst,
    EFVar,
    ELet,
    EMetaVar,
    EPi,
    ESort,
    Expr,
    UnivLevelIMax,
    UnivLevelParam,
    UnivLevelSucc,
    UnivLevelZero,
    app,
    lam,
    let_,
    pi,
)
from poussins.environment import AxiomDeclaration
from poussins.errors import KernelTypeError
from poussins.framework import create_environment, create_standard_environment
from poussins.kernel.proof_state import MetaVar
from poussins.kernel.typecheck import check_type, infer_metavar_types, infer_type


class TestInferType:
    """Mathematical soundness checks for `infer_type`."""

    prop: Final = ESort(UnivLevelZero())
    type0: Final = ESort(UnivLevelSucc(UnivLevelZero()))
    type1: Final = ESort(UnivLevelSucc(UnivLevelSucc(UnivLevelZero())))

    def test_sort_hierarchy_formation(self):
        """Sort hierarchy follows cumulative successor formation."""
        assert infer_type(self.prop, {}, {}) == self.type0
        assert infer_type(self.type0, {}, {}) == self.type1

    def test_variable_rule(self):
        """Variables are typed by context lookup."""
        context: dict[str, Expr] = {"x": self.prop}
        assert infer_type(EFVar("x"), context, {}) == self.prop

    def test_variable_rule_rejects_unbound_names(self):
        """Typing fails for unbound variables."""
        with pytest.raises(KernelTypeError):
            infer_type(EFVar("x"), {}, {})

    def test_constant_rule_with_universe_instantiation(self):
        """Polymorphic constants instantiate level parameters correctly."""
        env = create_environment()
        env.add(
            AxiomDeclaration(
                name="idTy",
                level_params=("u",),
                type=EPi("A", ESort(UnivLevelParam("u")), ESort(UnivLevelParam("u"))),
            )
        )
        inferred = infer_type(EConst("idTy", (UnivLevelZero(),)), {}, {}, env)
        assert inferred == EPi("A", self.prop, self.prop)

    def test_constant_rule_rejects_wrong_level_arity(self):
        """Typing fails when level arity does not match declaration."""
        env = create_environment()
        env.add(
            AxiomDeclaration(
                name="poly",
                level_params=("u", "v"),
                type=self.type0,
            )
        )
        with pytest.raises(
            KernelTypeError,
        ):
            infer_type(EConst("poly", (UnivLevelZero(),)), {}, {}, env)

    def test_constant_rule_falls_back_to_context(self):
        """When env has no declaration, constants are typed from the context."""
        context: dict[str, Expr] = {"c": self.prop}
        assert infer_type(EConst("c", ()), context, {}) == self.prop

    def test_constant_rule_rejects_unknown_constant(self):
        """Unknown constants are rejected."""
        with pytest.raises(KernelTypeError):
            infer_type(EConst("unknown", ()), {}, {})

    def test_pi_formation_rule(self):
        """Pi formation returns `Sort (imax u v)`."""
        expr = EPi("x", self.prop, self.prop)
        assert infer_type(expr, {}, {}) == ESort(
            UnivLevelIMax(
                UnivLevelSucc(UnivLevelZero()),
                UnivLevelSucc(UnivLevelZero()),
            )
        )

    def test_pi_formation_requires_sort_domain(self):
        """Pi formation rejects non-sort domains."""
        expr = EPi("x", EFVar("A"), self.prop)
        context: dict[str, Expr] = {"A": EFVar("B"), "B": self.prop}
        with pytest.raises(
            KernelTypeError,
        ):
            infer_type(expr, context, {})

    def test_pi_formation_requires_sort_body(self):
        """Pi formation rejects non-sort codomains."""
        expr = EPi("x", self.prop, EFVar("f"))
        context: dict[str, Expr] = {"f": EPi("y", self.prop, self.prop)}
        with pytest.raises(KernelTypeError):
            infer_type(expr, context, {})

    def test_lambda_introduction_rule(self):
        """Lambda introduction yields a Pi type."""
        expr = lam((("x", self.prop),), "x")
        assert infer_type(expr, {}, {}) == pi((("x", self.prop),), self.prop)

    def test_lambda_introduction_requires_well_formed_domain(self):
        """Lambda introduction rejects ill-formed binder domains."""
        expr = lam((("x", EFVar("A")),), "x")
        context: dict[str, Expr] = {"A": EFVar("B"), "B": self.prop}
        with pytest.raises(
            KernelTypeError,
        ):
            infer_type(expr, context, {})

    def test_typed_let_expression_infers_body_type(self):
        """Typed let expressions infer by checking annotation then opening body."""
        expr = let_("x", self.prop, EFVar("y"), "x")
        context: dict[str, Expr] = {"y": self.prop}
        assert infer_type(expr, context, {}) == self.prop

    def test_typed_let_expression_rejects_value_type_mismatch(self):
        """Typed let rejects values that do not match annotation."""
        expr = let_("x", self.type0, EFVar("y"), "x")
        context: dict[str, Expr] = {"y": self.prop}
        with pytest.raises(KernelTypeError):
            infer_type(expr, context, {})

    def test_typed_let_expression_requires_well_typed_annotation(self):
        """Typed let requires annotation itself to be a type."""
        expr = ELet("x", EFVar("A"), EFVar("y"), EBVar(0))
        context: dict[str, Expr] = {"A": EFVar("B"), "B": self.prop, "y": self.prop}
        with pytest.raises(KernelTypeError):
            infer_type(expr, context, {})

    def test_application_elimination_rule(self):
        """Application eliminates Pi by substituting the argument."""
        fn_type = pi((("x", self.prop),), "x")
        context: dict[str, Expr] = {
            "f": fn_type,
            "p": self.prop,
        }
        inferred = infer_type(EApp(EFVar("f"), EFVar("p")), context, {})
        assert inferred == EFVar("p")

    def test_application_rejects_non_function_head(self):
        """Application requires a Pi-typed head."""
        context: dict[str, Expr] = {"x": self.prop, "p": self.prop}
        with pytest.raises(KernelTypeError):
            infer_type(EApp(EFVar("x"), EFVar("p")), context, {})

    def test_application_rejects_domain_mismatch(self):
        """Application requires argument/domain definitional equality."""
        fn_type = pi((("x", self.type0),), "x")
        context: dict[str, Expr] = {
            "f": fn_type,
            "p": self.prop,
        }
        with pytest.raises(KernelTypeError):
            infer_type(EApp(EFVar("f"), EFVar("p")), context, {})

    def test_metavariable_rule(self):
        """Metavariables are typed by their declared statement."""
        metavars = {"m1": MetaVar(statement=self.prop)}
        assert infer_type(EMetaVar("m1"), {}, metavars) == self.prop

    def test_metavariable_rule_rejects_unknown_goal(self):
        """Typing fails for unknown metavariables."""
        with pytest.raises(KernelTypeError):
            infer_type(EMetaVar("m1"), {}, {})

    def test_cases_on_typing_checks_constructor_branches(self):
        """`casesOn` typing validates branch arity/types against constructors."""
        env = create_standard_environment()
        nat = EConst("Nat", ())
        motive = lam((("_n", nat),), nat)
        expr = app(
            EConst("Nat.casesOn", ()),
            EFVar("n"),
            motive,
            EConst("Nat.zero", ()),
            lam((("k", nat),), "k"),
        )
        context: dict[str, Expr] = {"n": nat}
        assert infer_type(expr, context, {}, env) == EApp(motive, EFVar("n"))

    def test_cases_on_typing_rejects_invalid_branch_type(self):
        """`casesOn` typing rejects branches that do not match constructor binders."""
        env = create_standard_environment()
        nat = EConst("Nat", ())
        motive = lam((("_n", nat),), nat)
        expr = app(
            EConst("Nat.casesOn", ()),
            EFVar("n"),
            motive,
            EConst("Nat.zero", ()),
            EConst("Nat.zero", ()),
        )
        context: dict[str, Expr] = {"n": nat}
        with pytest.raises(KernelTypeError):
            infer_type(expr, context, {}, env)

    def test_sigma_type_is_registered_in_standard_environment(self):
        """Sigma is available as a dependent inductive family."""
        env = create_standard_environment()
        sigma = EConst("Sigma", (UnivLevelZero(), UnivLevelZero()))
        assert env.get("Sigma") is not None
        assert infer_type(sigma, {}, {}, env) == EPi(
            "A",
            self.prop,
            EPi(
                "B",
                EPi("_", EBVar(0), self.prop),
                ESort(UnivLevelIMax(UnivLevelZero(), UnivLevelZero())),
            ),
        )


class TestCheckType:
    """Mathematical soundness checks for `check_type`."""

    prop: Final = ESort(UnivLevelZero())
    type0: Final = ESort(UnivLevelSucc(UnivLevelZero()))

    def test_conversion_rule(self):
        """Checking accepts types convertible to the inferred type."""
        expr = lam((("x", self.prop),), "x")
        expected = pi(
            (("y", EApp(lam((("T", self.type0),), "T"), self.prop)),),
            self.prop,
        )
        assert check_type(expr, expected, {}, {}) is True

    def test_cumulativity_rule_for_sorts(self):
        """Checking accepts universe cumulativity between sorts."""
        assert check_type(self.prop, self.type0, {}, {}) is True

    def test_rejects_incompatible_types(self):
        """Checking fails for incompatible expected types."""
        expr = lam((("x", self.prop),), "x")
        expected = pi((("x", self.type0),), "x")
        assert check_type(expr, expected, {}, {}) is False

    def test_rejects_non_cumulative_sort_direction(self):
        """Cumulativity is directional (`Type` does not check against `Prop`)."""
        assert check_type(self.type0, self.prop, {}, {}) is False

    def test_returns_false_when_inference_fails(self):
        """Checking returns False when inference raises a type error."""
        assert check_type(EFVar("x"), self.prop, {}, {}) is False


class TestInferMetaVarTypes:
    """Mathematical soundness checks for `infer_metavar_types`."""

    prop: Final = ESort(UnivLevelZero())

    def test_propagates_expected_domain_through_application(self):
        """Application structure propagates domain expectations to metavariables."""
        expr = EApp(EFVar("f"), EMetaVar("m1"))
        context: dict[str, Expr] = {"f": EPi("x", self.prop, self.prop)}
        result = infer_metavar_types(
            expr,
            self.prop,
            context,
            {"m1": MetaVar(self.prop)},
        )
        assert result["m1"] == self.prop

    def test_falls_back_to_outer_expected_type(self):
        """When local inference fails, fallback uses the outer expected type."""
        expr = EMetaVar("m1")
        expected = EPi("x", self.prop, self.prop)
        result = infer_metavar_types(expr, expected, {}, {"m1": MetaVar(self.prop)})
        assert result["m1"] == expected

    def test_falls_back_when_function_inference_fails(self):
        """When function inference fails under application, fallback still applies."""
        expr = EApp(EFVar("unknown_fn"), EMetaVar("m1"))
        expected = self.prop
        result = infer_metavar_types(expr, expected, {}, {"m1": MetaVar(self.prop)})
        assert result["m1"] == expected
