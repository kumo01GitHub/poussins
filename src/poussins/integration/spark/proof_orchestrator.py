"""Orchestrates the execution of proof tasks across a Spark cluster."""
from __future__ import annotations

from typing import TYPE_CHECKING, Final

from ...environment import Environment
from ...errors import SparkIntegrationError
from ...utils.logging import get_logger
from .proof_task import ProofTaskDAG
from .proof_task_executor import (
    ProofTaskExecutor,
    TaskExecutionResult,
)
from .serializer import ProofTaskSerializer

if TYPE_CHECKING:
    from pyspark.sql import SparkSession


class ProofOrchestrator:
    """Orchestrates distributed proof DAG execution across a Spark cluster."""

    def __init__(self, spark: SparkSession, env: Environment) -> None:
        """Initialize the orchestrator."""
        self.spark: Final[SparkSession] = spark
        self.env: Final[Environment] = env
        self.logger = get_logger(__name__)

    def run(self, dag: ProofTaskDAG) -> Environment:
        """Execute the proof DAG stage by stage, broadcasting Environment updates."""
        current_env = self.env
        stages = dag.compute_execution_stages()
        self.logger.info(
            f"Starting orchestrator run for DAG with {len(stages)} execution stages"
        )

        for stage_idx, stage in enumerate(stages):
            self.logger.info(
                f"Executing Stage {stage_idx + 1}/{len(stages)} with {len(stage)} tasks"
            )

            broadcast_env = self.spark.sparkContext.broadcast(current_env)

            try:
                serialized_tasks = [
                    ProofTaskSerializer.serialize_node(node) for node in stage
                ]
                rdd = self.spark.sparkContext.parallelize(serialized_tasks)

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
                        + f" at stage {stage_idx + 1}: {res['error_message']}"
                    )
                    self.logger.error(error_msg)
                    raise SparkIntegrationError(error_msg)

                current_env.add(res["declaration"])
                self.logger.info(
                    f"Registered declaration for theorem '{res['task_name']}'"
                   + "into Driver Environment"
                )

        self.logger.info("Successfully executed all tasks in proof DAG")
        return current_env
