"""Example 2: Demonstrates the use of Or introduction rules in propositional logic."""
from poussins.framework import Example, Prop, create_standard_environment

env = create_standard_environment()
p, q = Prop("P", env), Prop("Q", env)


example1 = Example(p >> (p | q), env)

example1.intro("hP")
example1.left()
example1.exact("hP")

example1.qed()


example2 = Example(q >> (p | q), env)

example2.intro("hQ")
example2.right()
example2.exact("hQ")

example2.qed()


example3 = Example(p >> (q >> (p & q)), env)

example3.intros(["hP", "hQ"])
example3.split()
example3.exact("hP")
example3.exact("hQ")

example3.qed()
