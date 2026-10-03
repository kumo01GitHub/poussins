"""Verification script for a dependency-based proof DAG with two lemmas."""

from __future__ import annotations

from pyspark.sql import SparkSession

from poussins import Environment, Nat, Prop
from poussins.integration.spark import ProofRunner, ProofTaskRegistry
from poussins.utils.logging import get_logger


def main() -> None:
    """Prove a conjunction theorem built from two dependent lemmas."""
    logger = get_logger(__name__)

    logger.info("=== 1. Initializing SparkSession for Local Spark Cluster ===")
    spark = (
        SparkSession.builder
        .appName("Poussins-Local-Verification-v4.3")
        .master("spark://localhost:7077")
        .getOrCreate()
    )
    runner = ProofRunner(spark)

    logger.info("=== 2. Registering dependent proof tasks ===")
    env = Environment.standard()
    registry = ProofTaskRegistry()

    lemma1_prop = Prop(
        Nat.eq(Nat.add(Nat.zero(), Nat.zero()), Nat.zero())
    )
    lemma2_prop = Prop(
        Nat.eq(
            Nat.add(Nat.zero(), Nat.succ(Nat.zero())),
            Nat.succ(Nat.zero()),
        )
    )
    theorem_prop = lemma1_prop & lemma2_prop

    registry.register_task(
        name="lemma1",
        statement=lemma1_prop.expr,
        tactic_plan=[("rfl", {})],
    )
    registry.register_task(
        name="lemma2",
        statement=lemma2_prop.expr,
        tactic_plan=[("rfl", {})],
    )
    registry.register_task(
        name="theorem",
        statement=theorem_prop.expr,
        tactic_plan=[
            ("constructor", {}),
            ("exact", {"expr_or_name": "lemma1"}),
            ("exact", {"expr_or_name": "lemma2"}),
        ],
        depends_on=["lemma1", "lemma2"],
    )

    logger.info("=== 3. Executing distributed proof solve ===")
    try:
        final_env = runner.run(registry, env, main_theorem_name="theorem")

        theorem_decl = final_env.get("theorem")
        logger.info(f"🎉 Success! Theorem verified: {theorem_decl}")
    except Exception as e:
        logger.error(f"❌ Proof execution failed: {e}")
        raise
    finally:
        logger.info("=== 4. Stopping Spark Session ===")
        runner.stop()


if __name__ == "__main__":
    main()
