"""Module for running Spark-based proof execution pipelines."""

from __future__ import annotations

from typing import Self

from pyspark.sql import SparkSession

from ...environment import Environment
from .orchestrator import ProofOrchestrator
from .registry import ProofTaskRegistry


class ProofRunner:
    """High-level runner for executing distributed proof task DAGs on Spark.

    Manages the lifecycle of a SparkSession and orchestrates the proof execution flow.
    """

    def __init__(
        self,
        spark: SparkSession | None = None,
        app_name: str = "poussins",
    ) -> None:
        """Initialize the ProofRunner with an optional SparkSession."""
        self._external_spark = spark is not None
        if spark is not None:
            self.spark = spark
        else:
            self.spark = SparkSession.builder.appName(app_name).getOrCreate()

    def run(
        self,
        registry: ProofTaskRegistry,
        env: Environment | None = None,
        main_theorem_name: str = "main_theorem",
    ) -> Environment:
        """Execute all proof tasks in the DAG."""
        current_env = env if env is not None else Environment()
        dag = registry.build_dag()

        orchestrator = ProofOrchestrator(spark=self.spark, env=current_env)
        return orchestrator.run(dag, main_theorem_name=main_theorem_name)

    def stop(self) -> None:
        """Stop the SparkSession if it was created internally."""
        if not self._external_spark and hasattr(self, "spark"):
            self.spark.stop()

    def __enter__(self) -> Self:
        """Support for Context Manager pattern."""
        return self

    def __exit__(self, exc_type: object, exc_val: object, exc_tb: object) -> None:
        """Ensure Spark session is stopped when exiting with-block."""
        self.stop()
