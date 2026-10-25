"""Example 9: Practical demonstration of quotient types using apply."""
from poussins.framework import (
    Example,
    Quot,
    create_standard_environment,
)
from poussins.framework.definitions import Eq
from poussins.framework.inductive_types import Nat

env = create_standard_environment()

x = Nat("x")
y = Nat("y")
rel_def = Eq(env, "NMod3", (x, y), Nat.type_expr(), x % Nat(3), y % Nat(3))
rel_def.declare()

q_one = Quot[rel_def](Nat(7))
q_four = Quot[rel_def](Nat(4))

example = Example(Quot[rel_def].eq(q_one, q_four), env)
example.apply(Quot[rel_def].sound(Nat(7), Nat(4)))
example.rfl()
example.qed()
