"""Example demonstrating AI-driven TacticPlan generation and proof execution."""
from __future__ import annotations

from pathlib import Path

from poussins import Environment, Nat, Prop
from poussins.integration.pytorch import (
    AITacticPlanner,
    PyTorchProofScript,
    TacticTrainer,
)


def main() -> None:
    """Generate tactic plans using AI and verify proofs with PyTorchProofScript."""
    model_path = Path(__file__).resolve().parent / "models" / "tactic_model.pt"

    print(f"Loading trained AI model from: {model_path}")
    model, vocab = TacticTrainer.load_checkpoint(model_path)

    env = Environment.standard()
    planner = AITacticPlanner(model, vocab, env=env, max_depth=10, top_k=3)

    # 1. AI-driven proof of P -> (Q -> (P /\ Q))
    print("\n" + "=" * 60)
    print("Example 1: Proving P -> (Q -> (P /\\ Q)) with AI TacticPlan")
    print("=" * 60)

    p, q = Prop("P", env), Prop("Q", env)
    prop1 = p >> (q >> (p & q))

    print(f"Target Proposition: {prop1.expr}")
    ai_plan1 = planner.plan(prop1.expr, env=env)
    print("Generated Tactic Plan by PyTorch AI:")
    for step_num, (tactic_name, kwargs) in enumerate(ai_plan1, 1):
        print(f"  Step {step_num}: {tactic_name}({kwargs})")

    # Verify execution with PyTorchProofScript
    script1 = PyTorchProofScript(prop1.expr, env, name="ai_thm_and_intro")
    script1.execute_plan(ai_plan1)
    decl1 = script1.qed()
    print(f"Successfully Verified and Closed! Declared: {decl1.name}: {decl1.type}")

    # 2. AI-driven proof of 0 + 0 = 0
    print("\n" + "=" * 60)
    print("Example 2: Proving 0 + 0 = 0 with AI TacticPlan")
    print("=" * 60)

    zero_eq_zero = Prop(Nat.eq(Nat.add(Nat.zero(), Nat.zero()), Nat.zero())).expr
    print(f"Target Proposition: {zero_eq_zero}")
    ai_plan2 = planner.plan(zero_eq_zero, env=env)
    print("Generated Tactic Plan by PyTorch AI:")
    for step_num, (tactic_name, kwargs) in enumerate(ai_plan2, 1):
        print(f"  Step {step_num}: {tactic_name}({kwargs})")

    script2 = PyTorchProofScript(zero_eq_zero, env, name="ai_thm_zero_eq_zero")
    script2.execute_plan(ai_plan2)
    decl2 = script2.qed()
    print(f"Successfully Verified and Closed! Declared: {decl2.name}: {decl2.type}")

    # 3. AI-driven proof using auto_prove helper
    print("\n" + "=" * 60)
    print("Example 3: Proving P -> P using script.auto_prove()")
    print("=" * 60)

    id_prop = (p >> p).expr
    script3 = PyTorchProofScript(id_prop, env, name="ai_thm_id")
    plan3 = script3.auto_prove(planner)
    print(f"Synthesized Plan: {plan3}")
    decl3 = script3.qed()
    print(f"Successfully Verified and Closed! Declared: {decl3.name}: {decl3.type}")


if __name__ == "__main__":
    main()
