# Poussins Distributed Proof Execution Example (Spark)

This directory contains a verification script for distributed proof execution using Apache Spark with Poussins.

## Prerequisites

- Docker and Docker Compose
- Python 3.12+ (for running the host script)

## Execution Procedure

### 1. Start Spark Cluster via Docker Compose

Start the local Spark master and worker containers:

```bash
docker compose up -d
```

**Note:** Ensure the Spark master container exposes port 7077 to localhost:7077.

### 2. Run Verification Script

Execute the distributed proof verification script on the host environment:

```bash
python example/spark/example.py
```
