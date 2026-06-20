"""
Propositional logic example using poussins DSL.
"""

from poussins import Lemma, Prop, Environment

a, b = Prop("A"), Prop("B")

example_and = Lemma("Example1", a >> (b >> (a & b)))

example_and.intros(["ha", "hb"])
example_and.split()
example_and.exact("ha")
example_and.exact("hb")
example_and.qed(Environment())
