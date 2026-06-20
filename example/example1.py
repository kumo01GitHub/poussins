"""
Propositional logic example using poussins DSL.
"""

from poussins import Lemma, Prop, Environment

a, b = Prop("A"), Prop("B")

example1 = Lemma("Example1", a >> (b >> (a & b)))

example1.intros(["ha", "hb"])
example1.constructor()
example1.exact("ha")
example1.exact("hb")
example1.qed(Environment())
