"""
Propositional logic example using poussins DSL.
"""

from poussins.framework import Lemma, Prop
from poussins.framework.environment import Environment

a, b, c = Prop("A"), Prop("B"), Prop("C")

hilbert_s = Lemma("HilbertS", ((a >> (b >> c)) >> ((a >> b) >> (a >> c))).formula)

hilbert_s.intros(["habc", "hab", "ha"])
hilbert_s.apply("habc")
hilbert_s.exact("ha")
hilbert_s.apply("hab")
hilbert_s.exact("ha")
hilbert_s.qed(Environment())
