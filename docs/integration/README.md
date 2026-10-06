# Integration Guides

This section is for users and maintainers who need to run Poussins beyond a single local Python process, especially in distributed clusters or AI-driven proof synthesis environments.

## Who This Is For

Use these guides if you want to:
- run proof tasks in a parallel or distributed execution environment
- integrate Poussins with external compute backends such as Apache Spark
- train and execute neural policy models with PyTorch to automatically synthesize tactic plans (`TacticPlan`)
- evaluate large-scale independent proof jobs without rewriting the core proof DSL

If you are writing proofs in the main DSL, start with the [Proof Author Guide](../proof-author-guide.md). If you are extending the internals of the system, start with the [Developer Guide](../developer-guide.md).

## Index

- [Spark Integration Guide](spark.md): distributed proof execution with Apache Spark
- [PyTorch Integration Guide](pytorch.md): AI-driven tactic plan synthesis and neural proof automation

## Why This Index Lives Here

The integration docs sit one level below the main project documentation because they target specific execution and machine learning workloads rather than the core proof-authoring DSL. The root README remains the most visible entry point for all users, while this section collects feature-specific deployment and execution guides.
