"""Mathematical soundness tests for `poussins.kernel.typecheck`."""
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
    Expr,
    UnivLevelIMax,
    UnivLevelParam,
    UnivLevelSucc,
    UnivLevelZero,
)
from poussins.environment import AxiomDeclaration, Environment
from poussins.errors import KernelTypeError
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
        assert infer_type(EVar("x"), context, {}) == self.prop

    def test_variable_rule_rejects_unbound_names(self):
        """Typing fails for unbound variables."""
        with pytest.raises(KernelTypeError):
            infer_type(EVar("x"), {}, {})

    def test_constant_rule_with_universe_instantiation(self):
        """Polymorphic constants instantiate level parameters correctly."""
        env = Environment()
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
        env = Environment()
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
        expr = EPi("x", EVar("A"), self.prop)
        context: dict[str, Expr] = {"A": EVar("B"), "B": self.prop}
        with pytest.raises(
            KernelTypeError,
        ):
            infer_type(expr, context, {})

    def test_pi_formation_requires_sort_body(self):
        """Pi formation rejects non-sort codomains."""
        expr = EPi("x", self.prop, EVar("f"))
        context: dict[str, Expr] = {"f": EPi("y", self.prop, self.prop)}
        with pytest.raises(KernelTypeError):
            infer_type(expr, context, {})

    def test_lambda_introduction_rule(self):
        """Lambda introduction yields a Pi type."""
        expr = ELam("x", self.prop, EVar("x"))
        assert infer_type(expr, {}, {}) == EPi("x", self.prop, self.prop)

    def test_lambda_introduction_requires_well_formed_domain(self):
        """Lambda introduction rejects ill-formed binder domains."""
        expr = ELam("x", EVar("A"), EVar("x"))
        context: dict[str, Expr] = {"A": EVar("B"), "B": self.prop}
        with pytest.raises(
            KernelTypeError,
        ):
            infer_type(expr, context, {})

    def test_application_elimination_rule(self):
        """Application eliminates Pi by substituting the argument."""
        fn_type = EPi("x", self.prop, EVar("x"))
        context: dict[str, Expr] = {
            "f": fn_type,
            "p": self.prop,
        }
        inferred = infer_type(EApp(EVar("f"), EVar("p")), context, {})
        assert inferred == EVar("p")

    def test_application_rejects_non_function_head(self):
        """Application requires a Pi-typed head."""
        context: dict[str, Expr] = {"x": self.prop, "p": self.prop}
        with pytest.raises(KernelTypeError):
            infer_type(EApp(EVar("x"), EVar("p")), context, {})

    def test_application_rejects_domain_mismatch(self):
        """Application requires argument/domain definitional equality."""
        fn_type = EPi("x", self.type0, EVar("x"))
        context: dict[str, Expr] = {
            "f": fn_type,
            "p": self.prop,
        }
        with pytest.raises(KernelTypeError):
            infer_type(EApp(EVar("f"), EVar("p")), context, {})

    def test_metavariable_rule(self):
        """Metavariables are typed by their declared statement."""
        metavars = {"m1": MetaVar(statement=self.prop)}
        assert infer_type(EMetaVar("m1"), {}, metavars) == self.prop

    def test_metavariable_rule_rejects_unknown_goal(self):
        """Typing fails for unknown metavariables."""
        with pytest.raises(KernelTypeError):
            infer_type(EMetaVar("m1"), {}, {})

    def test_match_typing_current_kernel_rule(self):
        """Current match typing returns motive application to discriminee."""
        motive = ELam("n", self.prop, self.type0)
        expr = EMatch("Nat", EVar("n"), motive, (EVar("z"),))
        context: dict[str, Expr] = {"n": self.prop}
        assert infer_type(expr, context, {}) == EApp(motive, EVar("n"))


class TestCheckType:
    """Mathematical soundness checks for `check_type`."""

    prop: Final = ESort(UnivLevelZero())
    type0: Final = ESort(UnivLevelSucc(UnivLevelZero()))

    def test_conversion_rule(self):
        """Checking accepts types convertible to the inferred type."""
        expr = ELam("x", self.prop, EVar("x"))
        expected = EPi(
            "y",
            EApp(ELam("T", self.type0, EVar("T")), self.prop),
            self.prop,
        )
        assert check_type(expr, expected, {}, {}) is True

    def test_cumulativity_rule_for_sorts(self):
        """Checking accepts universe cumulativity between sorts."""
        assert check_type(self.prop, self.type0, {}, {}) is True

    def test_rejects_incompatible_types(self):
        """Checking fails for incompatible expected types."""
        expr = ELam("x", self.prop, EVar("x"))
        expected = EPi("x", self.type0, EVar("x"))
        assert check_type(expr, expected, {}, {}) is False

    def test_rejects_non_cumulative_sort_direction(self):
        """Cumulativity is directional (`Type` does not check against `Prop`)."""
        assert check_type(self.type0, self.prop, {}, {}) is False

    def test_returns_false_when_inference_fails(self):
        """Checking returns False when inference raises a type error."""
        assert check_type(EVar("x"), self.prop, {}, {}) is False


class TestInferMetaVarTypes:
    """Mathematical soundness checks for `infer_metavar_types`."""

    prop: Final = ESort(UnivLevelZero())

    def test_propagates_expected_domain_through_application(self):
        """Application structure propagates domain expectations to metavariables."""
        expr = EApp(EVar("f"), EMetaVar("m1"))
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
        expr = EApp(EVar("unknown_fn"), EMetaVar("m1"))
        expected = self.prop
        result = infer_metavar_types(expr, expected, {}, {"m1": MetaVar(self.prop)})
        assert result["m1"] == expected
