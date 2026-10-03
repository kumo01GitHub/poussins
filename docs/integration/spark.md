# Spark Integration Guide

This guide documents the supported example for running Poussins proof tasks on Apache Spark.

## Overview

The Spark integration is intended for workloads where a proof script can be decomposed into independent tasks that may be scheduled and executed across multiple workers. Instead of requiring the whole proof session to run in a single process, the integration builds a Spark-backed execution path around the standard Poussins proof environment and task registry.

This is a pragmatic integration for distributed execution, not a replacement for the main proof-authoring interfaces. Most users should still write proofs through the standard DSL described in the [Proof Author Guide](../proof-author-guide.md). Use Spark when you want to scale execution of multiple proof tasks or evaluate a batch of independent verification jobs.

## Audience

This guide is aimed at:
- users who want to execute proof tasks on a local Spark cluster
- maintainers evaluating the distributed execution path
- integrators who need to adapt the execution pattern to a larger infrastructure

## Repository Layout

Relevant files in the repository:

- `example/spark/example*.py`: host-side Spark execution script
- `example/spark/compose.yaml`: local Spark cluster definition
- `example/spark/Dockerfile`: container image for the Spark workers
- `src/poussins/integration/spark/`: integration implementation for orchestrator, runner, registry, serializer, and task wrappers

## Prerequisites

Before running the example, make sure you have:

- Docker and Docker Compose
- Python 3.12+
- the project dependencies installed in your environment (for example, `uv sync` from the repository root)
- a local Docker network that can expose the Spark master on `localhost:7077`

## Quick Start

From the repository root:

```bash
cd example/spark
docker compose up -d
cd ../..
python example/spark/example.py
```

If you are using `uv`, the equivalent command is `uv run python example/spark/example.py`. The example starts a Spark master and workers, then submits a proof task workload through the Poussins Spark runner.

## Execution Flow

The distributed path follows the same proof model as the core library, but wraps proof tasks in a Spark-friendly execution layer:

1. The environment is prepared and serialized for distribution.
2. Proof tasks are registered in the task registry.
3. The orchestrator broadcasts the environment and partitions the task list.
4. Spark workers execute each task independently.
5. Results are collected and returned through the runner interface.

The goal is not to change the logic of proof validation itself; it is to distribute the execution of many separate tasks while preserving the same proof environment semantics.

## Example Script

The host-side script in `example/spark/example.py` configures a `SparkSession`, builds a `ProofRunner`, and submits proof tasks through the integration wrapper. The script is a practical reference implementation for local testing and a template for adapting the same flow to a larger cluster.

## Operational Notes

- The local example is designed for development and experimentation. It is not intended as a production cluster deployment blueprint.
- Proof tasks should be independent enough to be scheduled in parallel; tasks with strong interdependence should generally remain in a single-process proof workflow.
- The Spark integration is a distribution layer on top of the existing Poussins kernel and tactic system, not a separate proof calculus.

## Troubleshooting

- If the master is not reachable on `localhost:7077`, confirm that the containers are running and the correct port mapping is active.
- If the task runner fails to import dependency modules, ensure the project dependencies are installed in your active environment, including the Spark extra if needed: `python -m pip install .[spark]` or `uv sync`.
- If the proof workload hangs, check whether the worker containers are healthy and whether the task registry produced tasks that can be executed independently.

## Related Documentation

- [Integration Guides Index](README.md)
- [Proof Author Guide](../proof-author-guide.md)
- [Developer Guide](../developer-guide.md)
