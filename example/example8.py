"""Example 8: Demonstrates the use of existential and universal quantifiers in Poussins."""
from poussins.environment import Environment
from poussins.framework import Example, Nat, Prop

env = Environment.standard()

# ------------------------------------------------------------------
# Example 1:
#   Prove that if there exists a natural number n such that n + 0 = 0,
#   then we can use n = 0 to prove it.
# ------------------------------------------------------------------
statement1 = Prop.exists(
    (("n", Nat.type()),),
    Prop(Nat.eq(Nat.add(Nat("n"), Nat.zero()), Nat.zero()))
)
example1 = Example(statement1.expr, env)

example1.use(Nat.zero().expr)
example1.rfl()

example1.qed()


# ------------------------------------------------------------------
# Example 2:
#   Prove that for all natural numbers n, n + 0 = n.
# ------------------------------------------------------------------
statement2 = Prop.forall(
    (("n", Nat.type()),),
    Prop(Nat.eq(Nat.add(Nat.zero(), Nat("n")), Nat("n"))),
)
example2 = Example(statement2.expr, env)
example2.intro("n")
example2.simpl()
example2.rfl()

example2.qed()
