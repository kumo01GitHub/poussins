"""Example 4: Demonstrates the use of the bottom (false) proposition in Poussins."""
from poussins.environment import Environment
from poussins.framework import Example, Prop

env = Environment.standard()

example = Example(Prop.bottom() >> Prop("A", env), env)

example.intro("hFalse")
example.exfalso()
example.exact("hFalse")

example.qed()
