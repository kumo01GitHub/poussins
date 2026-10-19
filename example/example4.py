"""Example 4: Demonstrates the use of the bottom (false) proposition in Poussins."""
from poussins.framework import Example, Prop, create_standard_environment

env = create_standard_environment()

p, q = Prop("P"), Prop("Q")

# ------------------------------------------------------------------
# Example 1: Prove that from false, any proposition follows (ex falso quodlibet).
# ------------------------------------------------------------------
example1 = Example(
    Prop.forall((p,), Prop.bottom() >> p),
    env,
)

example1.intro("P")
example1.intro("hFalse")
example1.exfalso()
example1.exact("hFalse")

example1.qed()


# ------------------------------------------------------------------
# Example 2:
#   Prove that from false, any proposition follows (ex falso quodlibet)
#   using contradiction.
# ------------------------------------------------------------------
example2 = Example(
    Prop.forall((p,), Prop.bottom() >> p),
    env,
)

example2.intro("P")
example2.intro("hFalse")
example2.contradiction()

example2.qed()


# ------------------------------------------------------------------
# Example 3:
#   Prove that if P implies false, then P is false (i.e., P is not true).
# ------------------------------------------------------------------
example3 = Example(
    Prop.forall(
        (p, q,),
        p >> ((p >> Prop.bottom()) >> q)),
    env
)

example3.intros(["P", "Q"])
example3.intro("hP")
example3.intro("hNotP")
example3.contradiction()

example3.qed()
