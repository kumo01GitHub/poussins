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

- `Environment.default()`: creates a default logic environment (`True`, `False`, `And`, `Or`, `Not`, `Nat`, `Bool`, `Prod`, `Option`, `List`, `Unit`, `Sum`, `Empty`, `Fin`, `Vector`, `Quot`)
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

You can call tactics as methods on `Example`/`Theorem`. The table below is the quick reference for the core proof steps.

| Tactic | Purpose | Notes |
| --- | --- | --- |
| `intro(name)` | Introduce one binder or hypothesis | Use when the goal is a Pi or implication. |
| `intros([names...])` | Introduce multiple binders/hypotheses | Convenient for chained implication goals. |
| `revert(hyp_names)` | Move hypotheses back into the goal as Pi binders | Useful when preparing a proof by generalization. |
| `exact(expr_or_name)` | Close the current goal with a term or local hypothesis | Equivalent to a direct proof term. |
| `assumption()` | Solve the goal from a matching local hypothesis | Common finishing step for simple goals. |
| `apply(expr_or_name)` | Apply a theorem or hypothesis to the goal | Produces subgoals for remaining premises. |
| `refine(expr)` | Refine the current goal with an expression containing metavariables | Useful when the shape is known but some terms are still placeholders. |
| `constructor(index=None)` | Apply a matching constructor | Optionally choose a specific constructor by index. |
| `cases(hypothesis_name)` | Split on an inductive hypothesis | Produces one branch per constructor. |
| `rcases(hyp_name, pattern)` | Recursively destruct an inductive hypothesis | Works well with nested constructor patterns. |
| `obtain(pattern, expr)` | Introduce a witness/proof and immediately destructure it | Handy for structured witness extraction. |
| `change(expr_or_name, hypothesis_name=None)` | Rewrite the current goal or hypothesis to a definitionally equal form | Useful when a proof goal needs to be aligned with a definitional reduction. |
| `simpl(...)` / `dsimp(...)` | Simplify the goal or hypothesis by reduction | Helps normalize expressions and eliminate definitional clutter. |
| `unfold(name, hypothesis_name=None)` | Unfold a definition in the goal or a local hypothesis | Good when the target depends on a reducible definition. |
| `exfalso()` | Change the target to `False` and prove contradiction first | Useful for indirect proofs. |
| `contradiction()` | Close the goal from contradictory hypotheses | Detects contradiction patterns such as `False` or mutually incompatible assumptions. |
| `induction(hypothesis_name)` | Apply structural induction on an inductive hypothesis | Produces constructor-specific subgoals. |
| `reflexivity()` / `rfl()` | Solve an equality goal when both sides are definitionally equal | Standard for reflexive equalities. |
| `symmetry()` / `symm()` | Reverse an equality goal | Converts `a = b` into `b = a`. |
| `transitivity(middle)` / `trans(middle)` | Split an equality goal with an intermediate term | Useful for chaining equalities. |
| `rewrite(hyp_name)` / `rw(hyp_name)` | Rewrite using a local equality hypothesis | Replaces occurrences of the LHS with the RHS. |
| `have(hyp_name, expr)` | Prove an intermediate fact before continuing | Creates a subgoal for the intermediate statement. |
| `specialize(hyp_name, arg)` | Instantiate a dependent hypothesis with an argument | Produces the specialized form of the local assumption. |
| `suffices(hyp_name, expr)` | Assert a sufficient intermediate fact | Creates goals for the main proof using the fact and the fact itself. |
| `use(expr)` / `exists(expr)` | Provide a witness for an existential goal | Turns the goal into the predicate applied to the witness. |
| `undo()` | Roll back one proof step | Useful during interactive development and debugging. |

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
