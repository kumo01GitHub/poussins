"""Unit tests for integration serializers (ExprSerializer, TacticPlanSerializer)."""
from __future__ import annotations

import pytest

from poussins.ast import (
    EApp,
    EConst,
    ELam,
    EPi,
    ESort,
    EVar,
    UnivLevelParam,
    UnivLevelSucc,
    UnivLevelZero,
)
from poussins.integration.serializer import (
    ExprSerializer,
    TacticPlanSerializer,
    UnivLevelSerializer,
)
from poussins.integration.tactic import TacticPlan


def test_univ_level_round_trip() -> None:
    """Test serialization and deserialization of universe levels."""
    u_zero = UnivLevelZero()
    u_succ = UnivLevelSucc(u_zero)
    u_param = UnivLevelParam("u")

    for level in (u_zero, u_succ, u_param):
        encoded = UnivLevelSerializer.to_dict(level)
        restored = UnivLevelSerializer.from_dict(encoded)
        assert restored == level


def test_expr_round_trip() -> None:
    """Test serialization and deserialization of various AST expressions."""
    e_sort = ESort(UnivLevelZero())
    e_var = EVar("x")
    e_const = EConst("Nat.zero", ())
    e_pi = EPi("A", e_sort, e_var)
    e_lam = ELam("x", e_var, e_var)
    e_app = EApp(e_lam, e_const)

    for expr in (e_sort, e_var, e_const, e_pi, e_lam, e_app):
        encoded = ExprSerializer.to_dict(expr)
        restored = ExprSerializer.from_dict(encoded)
        assert restored == expr


def test_tactic_plan_round_trip_with_expr() -> None:
    """Round-trip tagged Expr payloads in tactic arguments."""
    plan: TacticPlan = ("exact", {"expr_or_name": EVar("lemma_base")})

    serialized = TacticPlanSerializer.serialize(plan)
    restored = TacticPlanSerializer.deserialize(serialized)

    assert restored[0] == "exact"
    assert isinstance(restored[1]["expr_or_name"], EVar)
    assert restored[1]["expr_or_name"] == EVar("lemma_base")


def test_tactic_plan_round_trip_with_patterns_and_frozenset() -> None:
    """Round-trip tuple patterns and frozenset in tactic arguments."""
    cases_plan: TacticPlan = (
        "cases",
        {"hyp_name": "h", "patterns": (("Nat.zero",), ("Nat.succ", "n"))},
    )
    simpl_plan: TacticPlan = (
        "simpl",
        {"hyp_name": None, "unfolding": frozenset({"Nat.add", "Nat.zero"})},
    )

    for plan in (cases_plan, simpl_plan):
        serialized = TacticPlanSerializer.serialize(plan)
        restored = TacticPlanSerializer.deserialize(serialized)
        assert restored == plan


def test_tactic_plan_serializer_validation_errors() -> None:
    """Ensure invalid payloads trigger appropriate errors."""
    with pytest.raises(ValueError, match="must include '__kind'"):
        TacticPlanSerializer.from_dict(
            {
                "tactic": "exact",
                "args": {"expr_or_name": {"untyped": "dict"}},
            }
        )

    with pytest.raises(ValueError, match="List tactic argument must contain only"):
        TacticPlanSerializer.from_dict(
            {
                "tactic": "intros",
                "args": {"names": ["h1", 123]},  # type: ignore[list-item]
            }
        )
