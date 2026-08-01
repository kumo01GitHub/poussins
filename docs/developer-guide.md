# Developer Guide

This guide explains the internal architecture of poussins and how the major modules interact.

For daily proof writing, see [Proof Author Guide](proof-author-guide.md).

## Local Setup

```bash
uv sync
uv run pytest
uv run ruff check .
uv run -m poussins --help
```

## Repository Structure

```text
src/poussins/
  ast/           # Core expression/universe data types and utilities
  environment/   # Declaration store and predefined logical environment
  kernel/        # Goal state, type checking/unification, proof state transitions
  tactics/       # User-facing tactical transformations over ProofManager
  framework/     # High-level DSL wrappers: Prop, Example, Theorem
  cli/           # Command-line entry points and converters
  errors/        # Domain-specific exception hierarchy
example/         # Executable proof scripts
tests/           # Test suite
```

## Folder Dependency Hierarchy

The package is organized as a directed acyclic dependency graph. Each layer depends on lower layers, but no layer depends back on a higher layer.

```mermaid
flowchart TD
    A[ast/] --> E[environment/]
    A --> K[kernel/]
    A --> T[tactics/]
    A --> F[framework/]
    E --> K
    E --> T
    E --> F
    K --> T
    K --> F
    T --> F
    X[errors/] --> E
    X --> K
    X --> T
    X --> F
    C[cli/] --> F
    C --> T
```

In practice:

- `ast/` is the foundation layer. It defines expressions and utilities used everywhere.
- `errors/` is a shared support layer. It provides exception types used by the kernel, tactics, framework, and CLI.
- `environment/` builds on `ast/` and provides declarations for the kernel and framework.
- `kernel/` depends on `ast/`, `environment/`, and `errors/`, and is the core proof-state engine.
- `tactics/` depends on the kernel and framework-level concepts to transform goals.
- `framework/` builds on the kernel, tactics, environment, and ast to provide the user-facing DSL.
- `cli/` is the top-level entrypoint and depends on the framework and tactics layers.

This layout keeps the architecture layered and avoids circular imports.

## Design Principles

- Pure kernel state transitions: proof steps produce new immutable `ProofState` values.
- Thin tactics layer: tactics orchestrate `ProofManager`, while correctness is enforced by kernel checks.
- Friendly frontend DSL: `Prop`, `Example`, and `Theorem` hide kernel internals for users.
- Explicit environment model: declarations are registered in `Environment` and referenced by name.

## System Architecture

```mermaid
flowchart LR
    DSL[framework: Prop, Example, Theorem] --> Tactics[tactics: intro/apply/exact/...]
    Tactics --> Manager[kernel: ProofManager]
    Manager --> Engine[kernel: ProofEngine]
    Engine --> State[kernel: ProofState + MetaVars]
    Engine --> TC[kernel: infer_type + unify + whnf]
    Manager --> Env[environment: declarations]
    CLI[cli commands] --> DSL
```

## End-to-End Proof Flow

1. `Example` or `Theorem` is created with a target expression.
2. `ProofManager` builds an initial goal/metavariable state through `ProofEngine.create_initial_state`.
3. A tactic generates a candidate assignment and optional subgoals.
4. Kernel validates typing and definitional equality, then returns next immutable state.
5. Session history keeps state snapshots for `undo()`.
6. On `Theorem.qed()`, the final proof term is extracted and added to `Environment`.

## Key Components

### AST (`ast/`)

- Defines expression forms (`EVar`, `EConst`, `EPi`, `EApp`, `ELam`, `EMetaVar`, ...).
- Provides substitution/free-variable and metavariable helper utilities.

### Environment (`environment/`)

- Stores declarations (`ConstantDeclaration`, `InductiveDeclaration`, `ConstructorDeclaration`, ...).
- `Environment.default()` preloads basic logical primitives (`True`, `False`, `And`, `Or`, `Not`) and `Nat`.

### Kernel (`kernel/`)

- `ProofState`: immutable snapshot of current goals + metavariable assignments.
- `ProofEngine`: validates and applies `close_goal` / `refine_goal` transitions.
- `ProofManager`: stable facade used by tactics and framework.
- `typecheck.py`: inference, normalization (`whnf`), and unification core.

### Tactics (`tactics/`)

- Tactical operations are small adapters that:
  - read current goal
  - construct proof term skeletons
  - call `ProofManager` for verified state transitions
- `constructor` resolves inductive constructors from the environment and delegates to `apply`.
- `cases` performs a structural split over an inductive hypothesis and produces branch subgoals, which are then verified through the existing kernel refinement flow.

### Framework (`framework/`)

- `Prop` offers ergonomic proposition syntax via operators.
- `ProofScript` supplies fluent method-style tactic API.
- `Example` validates anonymous proofs.
- `Theorem` validates and registers named proofs into the environment.

## CLI Surface

Main entrypoint:

```bash
uv run -m poussins <subcommand>
```

Available subcommands:
- `prove <file>`: batch execution
- `step <file> [--theorem NAME]`: step-wise execution
- `lean2py <file> [--output FILE]`
- `py2lean <file> [--output FILE]`

## Extension Points

- Add a new tactic:
  - implement logic in `src/poussins/tactics/`
  - expose it through `framework/proof_script.py`
  - export it in `src/poussins/__init__.py`
  - add focused tests under `tests/`
- Add new logical constants/inductives:
  - extend environment declarations
  - ensure kernel typing/unification handles new cases

## Quality Checklist for Changes

- New/changed tactic has positive and negative tests.
- Error messages are specific (`TacticError`, `Kernel*Error`, `FrameworkError`).
- Public exports are updated if API is intended to be public.
- Examples still run with `uv run python example/...`.

---

Back to [README](../README.md).
