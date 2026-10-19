"""Example 8: Demonstrates the use of existential and universal quantifiers."""
from poussins.framework import Example, Prop, create_standard_environment
from poussins.framework.inductive_types import Nat

env = create_standard_environment()
n = Nat("n")

# ------------------------------------------------------------------
# Example 1:
#   Prove that if there exists a natural number n such that n + 0 = 0,
#   then we can use n = 0 to prove it.
# ------------------------------------------------------------------
statement1 = Prop.exists(
    (n,),
    Nat.eq(Nat.add(n, Nat.zero()), Nat.zero())
)
example1 = Example(statement1, env)

example1.use(Nat.zero())
example1.rfl()

example1.qed()


# ------------------------------------------------------------------
# Example 2:
#   Prove that for all natural numbers n, n + 0 = n.
# ------------------------------------------------------------------
statement2 = Prop.forall(
    (n,),
    Nat.eq(Nat.add(Nat.zero(), n), n),
)
example2 = Example(statement2, env)
example2.intro("n")
example2.simpl()
example2.rfl()

example2.qed()
