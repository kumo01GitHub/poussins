"""
"""
from poussins import Example, Prop


a, b, c = Prop("A"), Prop("B"), Prop("C")

example1 = Example((a | b) >> (b | a))
print(f"Statement: {example1.statement}")
example1.intro("h")
example1.cases("h")
example1.right()
example1.assumption()
example1.left()
example1.assumption()
example1.qed()
print(f"Assignment: {example1.assignment}")

example2 = Example((a & (b | c)) >> ((a & b) | (a & c)))
print(f"Statement: {example2.statement}")
example2.intro("h")
example2.cases("h", "ha", "hbc")
example2.cases("hbc", "hb", "hc")
example2.left()
example2.split()
example2.assumption()
example2.assumption()
example2.right()
example2.split()
example2.assumption()
example2.assumption()
example2.qed()
print(f"Assignment: {example2.assignment}")
