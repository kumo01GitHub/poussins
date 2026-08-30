"""Propositional logic example using poussins DSL.
"""
from poussins.environment import Environment
from poussins.framework import Example, Prop

env = Environment.standard()

p, q = Prop("P", env), Prop("Q", env)

example1 = Example(p >> (q >> (p & q)), env)

example1.intros(["hP", "hQ"])
example1.constructor()
example1.exact("hP")
example1.exact("hQ")

example1.qed()


example2 = Example(p >> p, env)

example2.intro("hP")
example2.assumption()

example2.qed()
