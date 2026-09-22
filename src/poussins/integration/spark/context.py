"""Module for managing Spark-based proof execution context."""
from __future__ import annotations

from typing import TYPE_CHECKING

from ...environment import Environment
from .aggregator import ProofAggregator
from .orchestrator import ProofOrchestrator
from .registry import ProofTaskRegistry

if TYPE_CHECKING:
    from pyspark.sql import SparkSession


class SparkProofContext:
    """High-level context for executing distributed proof tasks on Spark."""

    def __init__(self, spark: SparkSession) -> None:
        """Initialize context with an active SparkSession."""
        self.spark = spark

    @classmethod
    def get_or_create(cls, app_name: str = "poussins") -> SparkProofContext:
        """Create or retrieve a SparkSession and return a SparkProofContext instance."""
        spark = SparkSession.builder.appName(app_name).getOrCreate()
        return cls(spark)

    def solve(
        self,
        registry: ProofTaskRegistry,
        env: Environment | None = None,
        main_theorem_name: str = "main_theorem",
    ) -> Environment:
        """Execute all proof tasks registered in the registry and aggregate results."""
        current_env = env if env is not None else Environment()
        dag = registry.build_dag()

        orchestrator = ProofOrchestrator(spark=self.spark, env=current_env)
        declarations = orchestrator.run(dag)

        aggregator = ProofAggregator(current_env)
        return aggregator.assemble(
            declarations=declarations,
            main_theorem_name=main_theorem_name,
        )

    def stop(self) -> None:
        """Stop the underlying SparkSession."""
        self.spark.stop()
