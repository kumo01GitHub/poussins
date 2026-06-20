"""
Propositional logic example using poussins DSL.
"""

from poussins import Example, Prop

a, b, c, d = Prop("A"), Prop("B"), Prop("C"), Prop("D")

example1 = Example(a >> (a | b))
print(f"Statement: {example1.statement}")
example1.intro("ha")
example1.constructor(1)
example1.assumption()
example1.qed()
print(f"Assignment: {example1.assignment}")

example2 = Example(b >> (a | b))
print(f"Statement: {example2.statement}")
example2.intro("hb")
example2.constructor(2)
example2.assumption()
example2.qed()
print(f"Assignment: {example2.assignment}")

example3 = Example(a >> (b >> ((a | c) & (d | b))))
print(f"Statement: {example3.statement}")
example3.intros(["ha", "hb"])
example3.constructor()
example3.constructor()
example3.exact("ha")
example3.constructor(2)
example3.exact("hb")
example3.qed()
print(f"Assignment: {example3.assignment}")
