"""Example 3: Demonstrating the use of the Environment class in Poussins."""
from poussins.environment import Environment
from poussins.framework import Example, Prop

env = Environment.standard()

example1 = Example(Prop.top(), env)

example1.constructor()

example1.qed()
