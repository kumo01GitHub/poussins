"""Example 3: Demonstrating the use of the Environment class in Poussins."""
from poussins.framework import Example, Prop, create_standard_environment

env = create_standard_environment()

example1 = Example(Prop.top(), env)

example1.constructor()

example1.qed()
