"""
Propositional logic example using poussins DSL.
"""

from poussins import Example, Prop

a, b = Prop("A"), Prop("B")

example = Example(a >> (b >> (a & b)))
print(f"Statement: {example.statement}")

example.intros(["ha", "hb"])
example.constructor()
example.exact("ha")
example.exact("hb")
example.qed()
print(f"Assignment: {example.assignment}")
