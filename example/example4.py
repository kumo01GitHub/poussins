"""
Propositional logic example using poussins DSL.
"""
from poussins.environment import Environment
from poussins.framework import Example, Prop


env = Environment.standard()

example = Example(Prop.bottom() >> Prop("A", env), env)

example.intro("hFalse")
example.exfalso()
example.exact("hFalse")

example.qed()
