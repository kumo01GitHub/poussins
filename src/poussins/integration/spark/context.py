"""Module for managing Spark-based proof execution context."""
from __future__ import annotations

from typing import TYPE_CHECKING

from ...environment import Environment
from .proof_orchestrator import ProofOrchestrator
from .registry import ProofTaskRegistry

if TYPE_CHECKING:
    from pyspark.sql import SparkSession


class SparkProofContext:
    """High-level context for executing distributed proof tasks on Spark."""

    def __init__(self, spark: SparkSession) -> None:
        """Initialize context with an active SparkSession."""
        self.spark = spark

    @classmethod
    def get_or_create(cls, app_name: str = "PoussinsSparkEngine") -> SparkProofContext:
        """Create or retrieve a SparkSession and return a SparkProofContext instance."""
        spark = SparkSession.builder.appName(app_name).getOrCreate()
        return cls(spark)

    def solve(
        self, registry: ProofTaskRegistry, env: Environment | None = None
    ) -> Environment:
        """Execute all proof tasks registered in the ProofTaskRegistry."""
        current_env = env if env is not None else Environment()
        dag = registry.build_dag()
        orchestrator = ProofOrchestrator(spark=self.spark, env=current_env)
        return orchestrator.run(dag)

    def stop(self) -> None:
        """Stop the underlying SparkSession."""
        self.spark.stop()
