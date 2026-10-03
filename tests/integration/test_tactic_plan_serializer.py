"""Tests for integration tactic plan serialization helpers."""
from __future__ import annotations

import pytest

from poussins.ast import EVar
from poussins.integration.tactic import TacticPlan, TacticPlanSerializer


class TestTacticPlanSerializer:
    """Behavior tests for tactic plan round-trip serialization."""

    def test_restores_expr_from_expr_or_name_argument(self) -> None:
        """Round-trip tagged Expr payloads in tactic arguments."""
        plan: TacticPlan = ("exact", {"expr_or_name": EVar("lemma_base")})

        restored = TacticPlanSerializer.deserialize(
            TacticPlanSerializer.serialize(plan)
        )

        assert isinstance(restored[1]["expr_or_name"], EVar)
        assert restored[1]["expr_or_name"] == EVar("lemma_base")

    def test_keeps_string_for_expr_or_name_argument(self) -> None:
        """Keep plain string payloads unchanged through round-trip."""
        plan: TacticPlan = ("exact", {"expr_or_name": "lemma_base"})

        restored = TacticPlanSerializer.deserialize(
            TacticPlanSerializer.serialize(plan)
        )

        assert restored[1]["expr_or_name"] == "lemma_base"
        assert isinstance(restored[1]["expr_or_name"], str)

    def test_restores_cases_patterns_as_tuples(self) -> None:
        """Restore `cases` pattern payload as tuple-of-tuples."""
        plan: TacticPlan = (
            "cases",
            {"hyp_name": "h", "patterns": (("Nat.zero",), ("Nat.succ", "n"))},
        )

        restored = TacticPlanSerializer.deserialize(
            TacticPlanSerializer.serialize(plan)
        )

        assert restored[1]["patterns"] == (("Nat.zero",), ("Nat.succ", "n"))
        assert isinstance(restored[1]["patterns"], tuple)
        assert isinstance(restored[1]["patterns"][0], tuple)

    def test_restores_rcases_pattern_as_nested_tuple(self) -> None:
        """Restore nested `rcases` pattern payload as nested tuples."""
        plan: TacticPlan = (
            "rcases",
            {"hyp_name": "h", "pattern": ("And.intro", "hp", ("Exists.intro", "w"))},
        )

        restored = TacticPlanSerializer.deserialize(
            TacticPlanSerializer.serialize(plan)
        )

        assert restored[1]["pattern"] == ("And.intro", "hp", ("Exists.intro", "w"))
        assert isinstance(restored[1]["pattern"], tuple)
        assert isinstance(restored[1]["pattern"][2], tuple)

    def test_restores_unfolding_as_frozenset(self) -> None:
        """Round-trip simpl unfolding payload as frozenset[str]."""
        plan: TacticPlan = (
            "simpl",
            {"hyp_name": None, "unfolding": frozenset({"Nat.add", "Nat.zero"})},
        )

        restored = TacticPlanSerializer.deserialize(
            TacticPlanSerializer.serialize(plan)
        )

        assert restored[1]["unfolding"] == frozenset({"Nat.add", "Nat.zero"})
        assert isinstance(restored[1]["unfolding"], frozenset)

    def test_emits_type_tags_for_non_json_native_types(self) -> None:
        """Emit explicit type tags for non-JSON-native values."""
        plan: TacticPlan = (
            "rcases",
            {"hyp_name": "h", "pattern": ("And.intro", "hp", ("Exists.intro", "w"))},
        )

        encoded = TacticPlanSerializer.to_dict(plan)
        args = encoded["args"]
        assert isinstance(args, dict)
        pattern = args["pattern"]
        assert isinstance(pattern, dict)
        kind = pattern.get("__kind")
        assert isinstance(kind, str)

        assert kind == "tuple"

    def test_rejects_untyped_dict_argument(self) -> None:
        """Reject untyped dict payloads without `__kind` tags."""
        with pytest.raises(ValueError, match="must include '__kind'"):
            TacticPlanSerializer.from_dict(
                {
                    "tactic": "exact",
                    "args": {"expr_or_name": {"type": "EVar", "name": "h"}},
                }
            )

    def test_rejects_non_string_list_argument(self) -> None:
        """Reject list payloads containing non-string values."""
        with pytest.raises(
            ValueError,
            match="List tactic argument must contain only strings",
        ):
            TacticPlanSerializer.from_dict(
                {
                    "tactic": "intros",
                    "args": {"names": ["h1", 1]},
                }
            )
