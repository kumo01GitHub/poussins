"""
Propositional logic example using poussins DSL.
"""
from poussins import Example, Prop


example = Example(Prop.bot() >> Prop("A"))
print(f"Statement: {example.statement}")
example.intro("hfalse")
example.exfalso()
example.exact("hfalse")
example.qed()
print(f"Assignment: {example.assignment}")
