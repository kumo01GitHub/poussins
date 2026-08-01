# Proof Author Guide

This guide explains how to write and run proofs with poussins.

## Who This Is For

Use this guide if you want to:
- Write propositions in the Python DSL
- Prove them interactively with tactics
- Register completed theorems in an environment

For implementation details, see [Developer Guide](developer-guide.md).

## Quick Start

```bash
uv sync
uv run python example/example1.py
```

## Core Workflow

1. Create an environment.
2. Declare proposition symbols.
3. Open an `Example` or `Theorem` proof script.
4. Apply tactics until no goals remain.
5. Call `qed()`.

## Framework API

The framework layer gives you a friendly interface:

- `Environment.default()`: creates a default logic environment (`True`, `False`, `And`, `Or`, `Not`, `Nat`)
- `Prop`: proposition DSL (`>>`, `&`, `|`, `~`, `Prop.top()`, `Prop.bottom()`)
- `Example(statement, env)`: anonymous proof (useful for exploration)
- `Theorem(name, statement, env)`: named proof; `qed()` registers it into the environment

### Minimal `Example`

```python
from poussins import Environment, Example, Prop

env = Environment.default()
p = Prop("P", env)

ex = Example(p >> p, env)
ex.intro("hP")
ex.assumption()
ex.qed()
```

## Tactics You Can Use

You can call tactics as methods on `Example`/`Theorem`:

- `intro(name)`: introduce one binder/hypothesis
- `intros([names...])`: introduce multiple binders
- `exact(expr_or_name)`: close current goal with a term/hypothesis
- `assumption()`: close goal from a matching local hypothesis
- `apply(expr_or_name)`: apply theorem/hypothesis and create subgoals
- `constructor(index=None)`: apply a matching constructor (or choose 1-based constructor index)
- `cases(hypothesis_name)`: split on an inductive hypothesis and create one subgoal per constructor
- `exfalso()`: change target to `False` and prove contradiction first
- `undo()`: rollback one proof step

## Proof Example 1: Conjunction Introduction

Goal: prove $P \to Q \to P \land Q$.

```python
from poussins import Environment, Theorem, Prop

env = Environment.default()
p, q = Prop("P", env), Prop("Q", env)

th = Theorem("and_intro", p >> q >> (p & q), env)
th.intros(["hP", "hQ"])
th.constructor()          # picks And.intro
th.exact("hP")
th.exact("hQ")
th.qed()
```

After `qed()`, `and_intro` is available from `env` as a reusable declaration.

## Proof Example 2: Case Splitting with `cases`

Goal: prove `True -> True` by splitting on the hypothesis.

```python
from poussins import Environment, Example, Prop

env = Environment.default()

ex = Example(Prop.top() >> Prop.top(), env)
ex.intro("hTrue")
ex.cases("hTrue")
ex.constructor()
ex.qed()
```

## Proof Example 3: Modus Ponens with `apply`

Goal: prove $(P \to Q) \to P \to Q$.

```python
from poussins import Environment, Theorem, Prop

env = Environment.default()
p, q = Prop("P", env), Prop("Q", env)

mp = Theorem("mp", (p >> q) >> p >> q, env)
mp.intros(["hPQ", "hP"])
mp.apply("hPQ")          # reduces goal Q to subgoal P
mp.exact("hP")
mp.qed()
```

## Method Style vs Function Style

Method style is easiest:

```python
th.intro("h")
```

Function style is equivalent and works on `ProofManager`:

```python
from poussins.tactics import intro

intro(th.manager, "h")
```

## Running Proof Files

### Run as a normal Python script

```bash
uv run python path/to/proofs.py
```

### Run through CLI

```bash
uv run -m poussins prove path/to/proofs.py
uv run -m poussins step path/to/proofs.py --theorem theorem_name
```

## Troubleshooting

- `TacticError`: the chosen tactic does not match the current goal shape.
- `KernelTypeError` / `KernelValueError`: the generated term or subgoals are not type-correct.
- Duplicate names in environment: theorem name or declaration name already exists.

When debugging, inspect your current script state and simplify one tactic step at a time.

---

Back to [README](../README.md).
