"""Example 6: Prove that if n = m, then n + k = m + k."""
from poussins.environment import Environment
from poussins.framework import Example, Nat, Prop

env = Environment.standard()
n, m, k = Nat("n"), Nat("m"), Nat("k")


# ------------------------------------------------------------------
# Example 1: Prove that if n = m, then n + k = m + k.
# ------------------------------------------------------------------
bindings1 = (
    ("n", Nat.type()),
    ("m", Nat.type()),
    ("k", Nat.type()),
)
statement1 = Prop.forall(
    bindings1,
    Prop(Nat.eq(n, m)) >> Prop(Nat.eq(n + k, m + k)),
)

example1 = Example(statement1, env)

example1.intros(["n", "m", "k", "h"])
example1.rewrite("h")
example1.rfl()

example1.qed()


#------------------------------------------------------------------
# Example 2: Prove that if n = m, then m = n (symmetry of equality).
# ------------------------------------------------------------------
bindings2 = (
    ("n", Nat.type()),
    ("m", Nat.type()),
)

statement2 = Prop.forall(
    bindings2,
    Prop(Nat.eq(n, m)) >> Prop(Nat.eq(m, n)),
)

example2 = Example(statement2, env)

example2.intros(["n", "m", "h"])
example2.symmetry()
example2.exact("h")

example2.qed()
