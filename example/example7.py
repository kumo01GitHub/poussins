"""Example of using the 'have' tactic for forward reasoning in Poussins."""
from poussins.environment import Environment
from poussins.framework import Lemma, Prop

env = Environment.standard()
p, q, r = Prop("P", env), Prop("Q", env), Prop("R", env)

trans = Lemma("Transitivity", (p >> q) >> ((q >> r) >> (p >> r)), env)

trans.intros(["hPQ", "hQR", "hP"])
trans.have("hQ", q.expr)
trans.apply("hPQ")
trans.exact("hP")
trans.apply("hQR")
trans.exact("hQ")

trans.qed()
