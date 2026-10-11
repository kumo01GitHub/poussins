"""Example 4: Demonstrates the use of the bottom (false) proposition in Poussins."""
from poussins.framework import Example, Prop, create_standard_environment

env = create_standard_environment()


# ------------------------------------------------------------------
# Example 1: Prove that from false, any proposition follows (ex falso quodlibet).
# ------------------------------------------------------------------
example1 = Example(
    Prop.forall(
        (("A", Prop("A").type()),),
        Prop.bottom() >> Prop("A")),
    env,
)

example1.intro("A")
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
    Prop.forall(
        (("A", Prop("A").type()),),
        Prop.bottom() >> Prop("A")),
    env,
)

example2.intro("A")
example2.intro("hFalse")
example2.contradiction()

example2.qed()


# ------------------------------------------------------------------
# Example 3:
#   Prove that if P implies false, then P is false (i.e., P is not true).
# ------------------------------------------------------------------
p, a = Prop("P"), Prop("A")

example3 = Example(
    Prop.forall(
        (("P", p.type()), ("A", a.type()),),
        p >> ((p >> Prop.bottom()) >> a)),
    env
)

example3.intros(["P", "A"])
example3.intro("hP")
example3.intro("hNotP")
example3.contradiction()

example3.qed()
