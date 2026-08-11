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

## Import Style

Prefer importing from the subpackage that owns the API.

- Use `poussins.environment` for `Environment`.
- Use `poussins.framework` for proof-authoring DSL objects such as `Prop`, `Nat`, `Example`, and `Theorem`.
- Use `poussins.tactics` only when you want function-style tactics instead of method-style proof scripts.
- Use `poussins.ast` and `poussins.kernel` only when you intentionally need low-level implementation APIs.

## Framework API

The framework layer gives you a friendly interface:

- `Environment.default()`: creates a default logic environment (`True`, `False`, `And`, `Or`, `Not`, `Nat`, `Bool`)
- `Prop`: proposition DSL (`>>`, `&`, `|`, `~`, `Prop.top()`, `Prop.bottom()`)
- `Example(statement, env)`: anonymous proof (useful for exploration)
- `Theorem(name, statement, env)`: named proof; `qed()` registers it into the environment

### Minimal `Example`

```python
from poussins.environment import Environment
from poussins.framework import Example, Prop

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
- `revert(hyp_names)`: revert hypothesis/hypotheses from the local context back into the goal statement as Pi-types
- `exact(expr_or_name)`: close current goal with a term/hypothesis
- `assumption()`: close goal from a matching local hypothesis
- `apply(expr_or_name)`: apply theorem/hypothesis and create subgoals
- `refine(expr)`: refine the current goal using an expression that may contain metavariables (e.g. `EMetaVar("m")`), creating new subgoals for each unsolved metavariable
- `constructor(index=None)`: apply a matching constructor (or choose 1-based constructor index)
- `cases(hypothesis_name)`: split on an inductive hypothesis and create one subgoal per constructor
- `change(expr_or_name, hypothesis_name=None)`: rewrite the current goal (or a named local hypothesis type) to a definitionally equal expression
- `exfalso()`: change target to `False` and prove contradiction first
- `induction(hypothesis_name)`: apply structural induction on an inductive hypothesis and create subgoals for each constructor
-　`reflexivity() / rfl()`: Solve an equality goal _a = b_ where both sides are definitionally equal (convertible via computation/definition expansion).
-　`rewrite(hyp_name) / rw(hyp_name)`: Rewrite occurrences of the LHS with the RHS in the current goal using a local equality hypothesis _h : a = b_.
- `undo()`: rollback one proof step

### Induction and the Nat DSL

The built-in Nat type can be constructed with the public Nat DSL:

```python
from poussins.environment import Environment
from poussins.framework import Example, Nat
from poussins.ast import EConst, EMetaVar
from poussins.kernel.goal import Goal

env = Environment.default()

example = Example(EConst("True", ()), env)
subgoal = Goal(statement=EConst("True", ()), context={"n": EConst("Nat", ())})
example.manager.refine_goal(EMetaVar(subgoal.id), [subgoal])

example.induction("n")
```

`Nat.zero()` and `Nat.succ(n)` are convenient constructors for the default Nat type. The induction tactic is not limited to Nat; it also works for other inductive declarations, creating one branch per constructor and adding induction hypotheses for recursive arguments when appropriate.

### Logical Helpers

For the default logical connectives, poussins also provides a few convenience tactics:

- `left()`: solve an `Or` goal by choosing the left branch (`Or.inl`)
- `right()`: solve an `Or` goal by choosing the right branch (`Or.inr`)
- `split()`: solve an `And` goal by applying `And.intro`

These are convenience wrappers around the constructor tactic and are intended for the standard environment shipped with poussins.

## Proof Example 1: Conjunction Introduction

Goal: prove $P \to Q \to P \land Q$.

```python
from poussins.environment import Environment
from poussins.framework import Prop, Theorem

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
from poussins.environment import Environment
from poussins.framework import Example, Prop

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
from poussins.environment import Environment
from poussins.framework import Prop, Theorem

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
