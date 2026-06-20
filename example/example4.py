"""
Propositional logic example using poussins DSL.
"""

from poussins import Theorem, Example, Prop, Environment

a, b, c, d = Prop("A"), Prop("B"), Prop("C"), Prop("D")
env = Environment()

th = Theorem("Sample", a >> (b >> ((a | c) & (d | b))))
print(f"Statement: {th.statement}")
th.intros(["ha", "hb"])
th.constructor()
th.constructor()
th.exact("ha")
th.constructor(2)
th.exact("hb")
th.qed(env)
print(f"Assignment: {th.assignment}")

example = Example(a >> (b >> ((a | c) & (d | b))))
print(f"Statement: {example.statement}")
example.import_env(env)
example.exact("Sample")
example.qed()
print(f"Assignment: {example.assignment}")
