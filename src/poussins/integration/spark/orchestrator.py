"""Orchestrates the execution and aggregation of proof tasks across a Spark cluster."""

from __future__ import annotations

from typing import Final

from pyspark.sql import SparkSession

from ...environment import Environment
from ...errors import SparkIntegrationError
from ...utils.logging import get_logger
from .task import ProofTaskDAG
from .task_executor import ProofTaskExecutor, TaskExecutionResult


class ProofOrchestrator:
    """Orchestrates the execution of proof tasks across Spark stages."""

    def __init__(self, spark: SparkSession, env: Environment) -> None:
        """Initialize the orchestrator."""
        self.spark: Final[SparkSession] = spark
        self.env: Final[Environment] = env
        self.logger = get_logger(__name__)

    def run(
        self,
        dag: ProofTaskDAG,
        main_theorem_name: str = "main_theorem",
    ) -> Environment:
        """Execute the proof DAG across Spark stages, aggregate declarations."""
        if not dag.has_task(main_theorem_name):
            raise SparkIntegrationError(
                f"Main theorem task '{main_theorem_name}' is not registered"
                + " in the proof DAG."
            )

        if self.env.get(main_theorem_name) is not None:
            raise SparkIntegrationError(
                f"Theorem '{main_theorem_name}' already exists"
                + " in the provided Environment."
            )

        stages = dag.compute_execution_stages()

        self.logger.info(
            f"Starting orchestrator run for DAG with {len(stages)} execution stages"
        )

        for stage_idx, stage in enumerate(stages):
            self.logger.info(
                f"Executing Stage {stage_idx + 1}/{len(stages)} with {len(stage)} tasks"
            )

            broadcast_env = self.spark.sparkContext.broadcast(self.env)
            try:
                rdd = self.spark.sparkContext.parallelize(stage)
                results: list[TaskExecutionResult] = rdd.map(
                    lambda task, benv=broadcast_env: ProofTaskExecutor().execute_task(
                        task, benv.value
                    )
                ).collect()
            finally:
                broadcast_env.unpersist()

            for res in results:
                if not res["success"] or res["declaration"] is None:
                    error_msg = (
                        f"Proof task '{res['task_name']}' failed"
                        f" at stage {stage_idx + 1}: {res['error_message']}"
                    )
                    self.logger.error(error_msg)
                    raise SparkIntegrationError(error_msg)

                decl = res["declaration"]
                self.env.add(decl)
                self.logger.info(
                    f"Registered declaration for theorem '{res['task_name']}'"
                    " into staging Environment"
                )

        self.logger.info("Successfully executed all tasks in proof DAG.")
        return self.env
