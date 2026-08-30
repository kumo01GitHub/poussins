"""Propositional logic example using poussins DSL.
"""
from poussins.environment import Environment
from poussins.framework import Example, Prop

env = Environment.standard()

example1 = Example(Prop.top(), env)

example1.constructor()

example1.qed()
