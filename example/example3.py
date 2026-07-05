"""
Propositional logic example using poussins DSL.
"""
from poussins import Example, Prop


example1 = Example(Prop.top())
print(f"Statement: {example1.statement}")
example1.constructor()
example1.qed()
print(f"Assignment: {example1.assignment}")

example2 = Example(Prop.top())
print(f"Statement: {example2.statement}")
example2.exact("TOP")
example2.qed()
print(f"Assignment: {example2.assignment}")
