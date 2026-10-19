"""Example 1: A simple proof of the proposition P → (Q → (P ∧ Q))."""
from poussins.framework import Example, Prop, create_standard_environment

env = create_standard_environment()

p, q = Prop("P"), Prop("Q")

example1 = Example(
    Prop.forall(
        (p, q),
        p >> (q >> (p & q))
    ),
    env,
)

example1.intros(["P", "Q", "hP", "hQ"])
example1.constructor()
example1.exact("hP")
example1.exact("hQ")

example1.qed()


example2 = Example(
    Prop.forall((p,), p >> p),
    env,
)

example2.intro("P")
example2.intro("hP")
example2.assumption()

example2.qed()
