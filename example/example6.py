"""
Propositional logic example using poussins DSL.
"""
from poussins import Example, Prop


a = Prop("A")

example1 = Example(a >> Prop.top())
print(f"Statement: {example1.statement}")
example1.intro("ha")
example1.trivial()
example1.qed()
print(f"Assignment: {example1.assignment}")

example2 = Example(a >> (Prop.top() & a))
print(f"Statement: {example2.statement}")
example2.intro("ha")
example2.constructor()
example2.trivial()
example2.trivial()
example2.qed()
print(f"Assignment: {example2.assignment}")
