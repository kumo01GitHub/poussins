"""Example 8: Basic usage example of 'exists' and 'use' tactics."""
from poussins.environment import Environment
from poussins.framework import Example, Nat, Prop

env = Environment.standard()

bindings = (("m", Nat.type()),)
statement = Prop.exists(
    bindings,
    Prop(Nat.eq(Nat.add(Nat("m"), Nat.zero()), Nat.zero()))
)
example = Example(statement.expr, env)

example.use(Nat.zero().expr)
example.rfl()

example.qed()
