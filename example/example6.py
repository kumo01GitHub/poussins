"""Example proof demonstrating equality and addition properties for natural numbers.
"""
from poussins.environment import Environment
from poussins.framework import Example, Nat, Prop

env = Environment.standard()

n, m, k = Nat("n"), Nat("m"), Nat("k")

statement = Prop.forall(
    ("n", Nat.type()),
    ("m", Nat.type()),
    ("k", Nat.type()),
    Prop(Nat.eq(n, m)) >> Prop(Nat.eq(n + k, m + k)),
)

example = Example(statement, env)

example.intros(["n", "m", "k", "h"])

example.rewrite("h")
example.rfl()

example.qed()
