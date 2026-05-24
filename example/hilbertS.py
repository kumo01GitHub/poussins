"""
Propositional logic example using poussins DSL.
"""

from poussins.dsl import Lemma, Prop

a, b, c = Prop("A"), Prop("B"), Prop("C")

hilbert_s = Lemma("HilbertS", ((a >> (b >> c)) >> ((a >> b) >> (a >> c))).formula)

hilbert_s.intro("habc")
hilbert_s.intro("hab")
hilbert_s.intro("ha")
hilbert_s.apply("habc")
hilbert_s.exact("ha")
hilbert_s.apply("hab")
hilbert_s.exact("ha")
hilbert_s.qed()
