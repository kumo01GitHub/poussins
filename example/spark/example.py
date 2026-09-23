"""Verification script for Poussins distributed proof execution on Spark."""

from __future__ import annotations

from pyspark.sql import SparkSession

from poussins import Environment, Nat, Prop
from poussins.integration.spark import ProofTaskRegistry, SparkProofContext
from poussins.utils.logging import get_logger


def main() -> None:
    """Verify a simple proof using Poussins on a local Spark cluster."""
    logger = get_logger(__name__)

    logger.info("=== 1. Initializing SparkSession for Local Spark Cluster ===")
    spark = (
        SparkSession.builder
        .appName("Poussins-Local-Verification-v4.2")
        .master("spark://localhost:7077")
        .getOrCreate()
    )
    psc = SparkProofContext(spark)

    logger.info("=== 2. Setting up Environment and Task Registry ===")
    env = Environment.standard()
    registry = ProofTaskRegistry()

    stmt_lemma = Prop(
        Nat.eq(Nat.add(Nat.zero(), Nat.zero()), Nat.zero())
    ).expr

    registry.register_task(
        name="lemma_base",
        statement=stmt_lemma,
        tactic_recipe=[
            ("rfl", {})
        ]
    )

    registry.register_task(
        name="main_theorem",
        statement=stmt_lemma,
        tactic_recipe=[
            ("exact", {"expr_or_name": "lemma_base"})
        ],
        depends_on=["lemma_base"]
    )

    logger.info("=== 3. Executing Distributed Proof Solve ===")
    try:
        final_env = psc.solve(registry, env, main_theorem_name="main_theorem")

        main_decl = final_env.get("main_theorem")
        logger.info(f"🎉 Success! Main theorem verified: {main_decl}")
    except Exception as e:
        logger.error(f"❌ Proof execution failed: {e}")
        raise
    finally:
        logger.info("=== 4. Stopping Spark Session ===")
        psc.stop()


if __name__ == "__main__":
    main()
