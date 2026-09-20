"""Example 4: Demonstrates the use of the bottom (false) proposition in Poussins."""
from poussins.environment import Environment
from poussins.framework import Example, Prop

env = Environment.standard()


# ------------------------------------------------------------------
# Example 1: Prove that from false, any proposition follows (ex falso quodlibet).
# ------------------------------------------------------------------
example1 = Example(Prop.bottom() >> Prop("A", env), env)

example1.intro("hFalse")
example1.exfalso()
example1.exact("hFalse")

example1.qed()


# ------------------------------------------------------------------
# Example 2:
#   Prove that from false, any proposition follows (ex falso quodlibet)
#   using contradiction.
# ------------------------------------------------------------------
example2 = Example(Prop.bottom() >> Prop("B", env), env)

example2.intro("hFalse")
example2.contradiction()

example2.qed()


# ------------------------------------------------------------------
# Example 3:
#   Prove that if P implies false, then P is false (i.e., P is not true).
# ------------------------------------------------------------------
p = Prop("P", env)
c = Prop("C", env)

example2 = Example(p >> ((p >> Prop.bottom()) >> c), env)

example2.intro("hP")
example2.intro("hNotP")
example2.contradiction()

example2.qed()
