"""
Propositional logic example using poussins DSL.
"""
from poussins import Example, FTrue


example1 = Example(FTrue())
print(f"Statement: {example1.statement}")
example1.constructor()
example1.qed()
print(f"Assignment: {example1.assignment}")

example2 = Example(FTrue())
print(f"Statement: {example2.statement}")
example2.exact("TOP")
example2.qed()
print(f"Assignment: {example2.assignment}")
