# Proof Author Guide

This guide explains how to write and run proofs with poussins.

## Who This Is For

Use this guide if you want to:
- Write propositions in the Python DSL
- Prove them interactively with tactics
- Register completed theorems in an environment
- Define custom inductive types, definitions, and quotient types

For implementation details, see [Developer Guide](developer-guide.md).

## Quick Start

```bash
uv sync
uv run python example/example1.py
```

## Core Workflow

1. Create an environment (`create_standard_environment()`).
2. Declare proposition symbols (`Prop("P")`), types (`Type("T")`), or inductive variables (`Nat("n")`).
3. Open an `Example` or `Theorem` proof script.
4. Apply tactics until no goals remain.
5. Call `qed()`.

## Import Style

Prefer importing from the subpackage that owns the API. The root package `poussins` is intentionally minimal.

- Use `poussins.environment` for `Environment`, declaration specifications (`InductiveSpec`, `DefinitionSpec`, `AxiomSpec`, `TheoremSpec`), and operations like `const`.
- Use `poussins.framework` for proof-authoring DSL objects: `Prop`, `Type`, `Example`, `Theorem` (and aliases `Lemma`, `Proposition`, `Corollary`, `Fact`, `Remark`, `Property`), `Axiom`, `Definition`, `Inductive`, `Quot`, environment creators (`create_environment`, `create_standard_environment`), and declaration helpers (`declare_axiom`, `declare_definition`, `declare_theorem`, `declare_inductive`, `declare_quot`).
- Use `poussins.framework.inductive` for the `Inductive` base class and `@inductive_type` decorator.
- Use `poussins.framework.inductive_types` for built-in inductive types: `Nat`, `Bool`, `List`, `Vector`, `Fin`, `Prod`, `Sigma`, `Sum`, `Option`, `Unit`, `Empty`.
- Use `poussins.framework.definitions` for predefined definition helpers such as `Eq`.
- Use `poussins.tactics` only when you want function-style tactics instead of method-style proof scripts.
- Use `poussins.ast` and `poussins.kernel` only when you intentionally need low-level implementation APIs.

## Framework API

The framework layer gives you a friendly, expressive interface:

- `create_standard_environment()`: creates the standard logic environment (`True`, `False`, `And`, `Or`, `Not`, `Nat`, `Bool`, `Prod`, `Option`, `List`, `Unit`, `Sum`, `Empty`, `Fin`, `Vector`, `Quot`, `Eq`).
- `Prop(name_or_expr)`: proposition DSL (`>>`, `&`, `|`, `~`, `Prop.top()`, `Prop.bottom()`). Supports quantifier construction:
  - `Prop.forall(bound_vars, body)`: universal quantification $\forall$. `bound_vars` can be passed as a single item or sequence of `Prop`, `Type`, `Inductive` instances, or `(name, type)` tuples. If `body` is omitted, it defaults to `Sort.PROP.sort`.
  - `Prop.exists(bound_vars, body)`: existential quantification $\exists$.
- `Type(name_or_expr, [level])`: universe-level type expression DSL (defaults to `Sort.TYPE.level`).
- `Inductive`: base class for inductive data types with `.eq(left, right)`, `.type_ref()`, `.type`, `.env()`, and bound variable semantics (`BindableMixin`). Configured via the `@inductive_type(spec)` decorator.
- `Nat`: natural numbers DSL under `poussins.framework.inductive_types`:
  - Construct with variable name (`Nat("n")`) or integer literal (`Nat(3)`).
  - Arithmetic constructors: `Nat.zero()`, `Nat.succ(n)`, `Nat.add(n, m)`, `Nat.sub(n, m)`, `Nat.mul(n, m)`, `Nat.div(n, m)`, `Nat.mod(n, m)`, `Nat.eq(n, m)`.
  - Operator overloading: `+`, `-`, `*`, `//`, `/`, `%`.
- `Quot[relation]`: quotient type DSL bound to an equivalence relation definition:
  - `Quot[rel_def](x)` / `Quot[rel_def].mk(x)`: construct canonical projection $\pi(x) = [x]$.
  - `Quot[rel_def].sound(a, b, [h])`: equality from relation proof ($a \sim b \implies [a] = [b]$).
  - `Quot[rel_def].lift(B, f, compat, q)`: lift a compatible function to the quotient.
  - `Quot[rel_def].ind(motive, h, q)`: induction on quotient terms.
  - `Quot[rel_def].eq(left, right)`: equality proposition between quotient elements.
- `Definition` & `definitions.Eq`: definition wrappers. `Eq(name, bound_vars, type_a, left, right)` creates equivalence relation definitions with `.declare(env)`.
- `Axiom`: proposition accepted without proof. `Axiom(name, statement)` with `.declare(env)`.
- `declare_inductive(env, spec)`: registers a custom inductive type with `InductiveSpec(name, type, constructors)` and derives its `.rec` recursor and `.casesOn` eliminator automatically.
- `declare_definition(env, spec)`: registers a definition with `DefinitionSpec(name, type, value)`.
- `declare_axiom(env, spec)`: registers an axiom with `AxiomSpec(name, statement)`.
- `declare_theorem(env, spec)`: registers a theorem with `TheoremSpec(name, statement, term)`.
- `declare_quot(env)`: registers quotient declarations into the environment.
- `Example(statement, env)`: anonymous proof (isolated in an environment copy, useful for exploration and test verification).
- `Theorem(name, statement, env)`: named proof; `qed()` registers the resulting `TheoremDeclaration` into the environment.

### Minimal `Example`

```python
from poussins.framework import Example, Prop, create_standard_environment

env = create_standard_environment()
p = Prop("P")

ex = Example(p >> p, env)
ex.intro("hP")
ex.assumption()
ex.qed()
```

## Tactics You Can Use

You can call tactics as methods on `Example`/`Theorem`. Tactic arguments accepting expressions (`via`, `type`, `at`, etc.) support `ExprLike = Expr | Prop | Inductive | str`, allowing you to pass propositions, inductive terms, or hypothesis/declaration names directly.

| Tactic | Purpose | Notes |
| --- | --- | --- |
| **1. Forward Reasoning & Context** | | |
| `intro(as_)` | Introduce one binder or hypothesis | Use when the goal is a Pi or implication. `as_` specifies the hypothesis name. |
| `intros(as_)` | Introduce multiple binders/hypotheses | Convenient for chained implication or quantifier goals. Accepts a list of names for `as_`. |
| `have(as_, type_)` | Prove an intermediate fact before continuing | Creates a subgoal for the intermediate statement and introduces it as `as_`. Accepts `ExprLike` for `type_`. |
| `obtain(pattern, via)` | Introduce a witness/proof and immediately destructure it | Handy for structured witness extraction from proof term `via`. |
| `specialize(at, via)` | Instantiate a dependent hypothesis with an argument | Produces the specialized form of local hypothesis `at` using argument `via`. |
| `revert(at)` | Move hypotheses back into the goal as Pi binders | Useful when preparing a proof by generalization. Accepts name or list of names. |
| `clear(at)` | Remove an unused local hypothesis from the context | Fails if the target or another hypothesis still depends on `at`. |
| **2. Backward Reasoning & Goal Reduction** | | |
| `apply(via)` | Apply a theorem or hypothesis to the goal | Produces subgoals for remaining premises. Accepts `ExprLike` (`Expr`, `Prop`, theorem name string). |
| `exact(via)` | Close the current goal with a term or local hypothesis | Equivalent to a direct proof term. Accepts `ExprLike`. |
| `refine(via)` | Refine the current goal with an expression containing metavariables | Useful when the shape is known but some terms are still placeholders. |
| `assumption()` | Solve the goal from a matching local hypothesis | Common finishing step for simple goals. |
| `suffices(as_, type_)` | Assert a sufficient intermediate fact | Creates goals for the main proof using the fact and the fact itself. |
| `constructor(index=None)` | Apply a matching constructor | Optionally choose a specific constructor by index. |
| `left()` | Select the left branch of a disjunction goal | Target goal must be a disjunction (`A ∨ B`). |
| `right()` | Select the right branch of a disjunction goal | Target goal must be a disjunction (`A ∨ B`). |
| `split()` | Split a conjunction goal into two subgoals | Target goal must be a conjunction (`A ∧ B`). |
| `use(via)` / `exists(via)` | Provide a witness for an existential goal | Turns the goal into the predicate applied to witness `via`. |
| **3. Destructuring & Case Analysis** | | |
| `cases(at, with_=None)` | Split on an inductive hypothesis | Produces one branch per constructor for hypothesis `at`. |
| `rcases(at, with_)` | Recursively destruct an inductive hypothesis | Works well with nested constructor patterns `with_` on hypothesis `at`. |
| `induction(at)` | Apply structural induction on an inductive hypothesis | Produces constructor-specific subgoals for hypothesis `at`. |
| **4. Equality, Reduction & Unfolding** | | |
| `reflexivity()` / `rfl()` | Solve an equality goal when both sides are definitionally equal | Computes weak head normal forms (including recursor reductions $\iota$-reduction and constant unfolding) to close reflexive equalities ($a = a$). |
| `symmetry()` / `symm()` | Reverse an equality goal | Converts `a = b` into `b = a`. |
| `transitivity(via)` / `trans(via)` | Split an equality goal with an intermediate term | Converts `a = c` into `a = b` and `b = c` using middle term `via`. |
| `rewrite(via, *, at=None, on=None, symm=False)` / `rw(...)` | Rewrite using an equality hypothesis or theorem | Replaces LHS with RHS using `via`. Can target hypothesis `at` or subexpression `on`. |
| `unfold(def_name, *, at=None)` | Unfold a definition in the goal or a local hypothesis | Good when goal or hypothesis `at` depends on reducible definition `def_name`. |
| `simpl(*, at=None, unfolding=None)` | Simplify the goal or hypothesis by reduction | Helps normalize expressions. Can specify allowed `unfolding` definitions. |
| `dsimp(*, at=None, unfolding=None)` | Definitional simplify without unnecessary expansions | Strict definitional reduction on goal or hypothesis `at`. |
| `change(via, *, at=None)` | Rewrite the current goal or hypothesis to a definitionally equal form | Aligns a proof target or hypothesis `at` with a definitional reduction `via`. |
| **5. Automation, Contradiction & Decision** | | |
| `exfalso()` | Change the target to `False` and prove contradiction first | Useful for indirect proofs. |
| `contradiction()` | Close the goal from contradictory hypotheses | Detects contradiction patterns such as `False` or mutually incompatible assumptions. |

### Quantifiers and Bound Variables

You can bind multiple propositions, types, or inductive variables cleanly using `Prop.forall` and `Prop.exists`:

```python
from poussins.framework import Example, Prop, create_standard_environment
from poussins.framework.inductive_types import Nat

env = create_standard_environment()
n = Nat("n")

# Universal quantification with bound Nat variable
statement = Prop.forall(
    (n,),
    Nat.eq(Nat.add(Nat.zero(), n), n),
)
ex = Example(statement, env)
ex.intro("n")
ex.rfl()
ex.qed()
```

### Induction and the Nat DSL

The built-in `Nat` type supports full arithmetic expressions and operator overloading:

```python
from poussins.framework import Example, Prop, create_standard_environment
from poussins.framework.inductive_types import Nat

env = create_standard_environment()
n = Nat("n")

# Induction on a natural number variable
statement = Prop.forall((n,), Nat.eq(n, n))
ex = Example(statement, env)
ex.intro("n")
ex.induction("n")  # generates subgoals for zero base case and succ inductive step
ex.rfl()
ex.rfl()
ex.qed()
```

`Nat.zero()`, `Nat.succ(n)`, `Nat(3)`, and arithmetic operators (`+`, `-`, `*`, `//`, `%`) construct valid expressions. The `induction` tactic works for all inductive declarations registered in `env`, creating one branch per constructor and adding induction hypotheses for recursive arguments.

### Logical Helpers

For default logical connectives, poussins provides convenience tactics:

- `left()`: solve an `Or` goal by choosing the left branch (`Or.inl`)
- `right()`: solve an `Or` goal by choosing the right branch (`Or.inr`)
- `split()`: solve an `And` goal by applying `And.intro`

These are convenience wrappers around `constructor` intended for the standard environment.

## Proof Example 1: Conjunction Introduction

Goal: prove $\forall P\ Q : \text{Prop},\ P \to Q \to P \land Q$.

```python
from poussins.framework import Example, Prop, create_standard_environment

env = create_standard_environment()
p, q = Prop("P"), Prop("Q")

ex = Example(
    Prop.forall(
        (p, q),
        p >> (q >> (p & q)),
    ),
    env,
)
ex.intros(["P", "Q", "hP", "hQ"])
ex.constructor()          # picks And.intro
ex.exact("hP")
ex.exact("hQ")
ex.qed()
```

## Proof Example 2: Case Splitting with `cases`

Goal: prove `True -> True` by splitting on the hypothesis.

```python
from poussins.framework import Example, Prop, create_standard_environment

env = create_standard_environment()

ex = Example(Prop.top() >> Prop.top(), env)
ex.intro("hTrue")
ex.cases("hTrue")
ex.constructor()
ex.qed()
```

## Proof Example 3: Modus Ponens with `apply`

Goal: prove $(P \to Q) \to P \to Q$.

```python
from poussins.framework import Prop, Theorem, create_standard_environment

env = create_standard_environment()
p, q = Prop("P"), Prop("Q")

mp = Theorem("mp", (p >> q) >> p >> q, env)
mp.intros(["hPQ", "hP"])
mp.apply("hPQ")          # reduces goal Q to subgoal P
mp.exact("hP")
mp.qed()
```

After `qed()`, `mp` is registered in `env` and can be referenced by subsequent proofs.

## Proof Example 4: Quotient Types and Definitional Equality

Goal: prove that $7 \equiv 4 \pmod 3$ implies $[7] = [4]$ in $\mathbb{N}/\sim_3$.

```python
from poussins.framework import Example, Quot, create_standard_environment
from poussins.framework.definitions import Eq
from poussins.framework.inductive_types import Nat

env = create_standard_environment()

x, y = Nat("x"), Nat("y")
# Define the equivalence relation: x ≡ y (mod 3) := (x % 3 = y % 3)
rel_def = Eq("NMod3", (x, y), Nat, x % Nat(3), y % Nat(3))
rel_def.declare(env)

# Create quotient values
q_four = Quot[rel_def](Nat(4))
q_seven = Quot[rel_def](Nat(7))

# Prove [7] = [4]
example = Example(Quot[rel_def].eq(q_seven, q_four), env)
example.apply(Quot[rel_def].sound(Nat(7), Nat(4)))
example.rfl()  # closes goal by computing 7 % 3 == 4 % 3 == 1 definitionally
example.qed()
```

## Defining Custom Inductive Types

You can define custom inductive types by decorating an `Inductive` subclass with `@inductive_type(spec)` and calling `.declare(env)`:

1. **Define the Specification (`InductiveSpec`)**:
   Specify the inductive type name, sort type, and constructors.
2. **Define the DSL Class with `@inductive_type`**:
   Decorate the `Inductive` subclass with `@inductive_type(spec=...)`. The decorator automatically sets the inductive metadata and constructor specifications.
3. **Define `.declare(env)` and Register**:
   Implement `.declare(env)` on the class using `declare_inductive(env, spec)` and setting `cls._env = env`. Calling `MyNat.declare(env)` registers the inductive type, all constructors, recursor (`.rec`), and `.casesOn` eliminator into `env`.

### Example: Custom Inductive Type with Induction

```python
from dataclasses import dataclass
from typing import ClassVar
from poussins.ast import EConst, Expr, Sort, app, pi
from poussins.environment import Environment, InductiveDeclaration, InductiveSpec, const
from poussins.framework import (
    Example,
    Inductive,
    Prop,
    create_standard_environment,
    declare_inductive,
)
from poussins.framework.inductive import inductive_type

env = create_standard_environment()

# 1. Define the inductive specification
my_nat_type = EConst("MyNat", ())
my_nat_spec = InductiveSpec(
    name="MyNat",
    type=Sort.TYPE.sort,
    constructors=(
        ("MyNat.zero", my_nat_type),
        ("MyNat.succ", pi((("n", my_nat_type),), my_nat_type)),
    ),
)

# 2. Define the DSL wrapper class decorated with @inductive_type
@dataclass(frozen=True, init=False)
@inductive_type(spec=my_nat_spec)
class MyNat(Inductive):
    ZERO_IDX: ClassVar[int] = 0
    SUCC_IDX: ClassVar[int] = 1

    @classmethod
    def declare(cls, env: Environment) -> InductiveDeclaration:
        decl = declare_inductive(env, my_nat_spec)
        cls._env = env
        return decl

    @classmethod
    def zero(cls) -> MyNat:
        env = cls.env()
        return cls(const(env=env, name=cls.CONSTRUCTORS[cls.ZERO_IDX][0]))

    @classmethod
    def succ(cls, n: MyNat | Expr) -> MyNat:
        env = cls.env()
        return cls(app(const(env=env, name=cls.CONSTRUCTORS[cls.SUCC_IDX][0]), cls.to_expr(n)))

# 3. Register the inductive type into the environment
MyNat.declare(env)

# 4. Use in interactive proofs with induction
n = MyNat("n")
ex = Example(Prop.forall((n,), MyNat.eq(n, n)), env)
ex.intro("n")
ex.induction("n")  # creates subgoals for zero base case and succ inductive step
ex.rfl()
ex.rfl()
ex.qed()
```

## Method Style vs Function Style

Method style is easiest:

```python
th.intro("h")
```

Function style is equivalent and works directly on `ProofManager`:

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
