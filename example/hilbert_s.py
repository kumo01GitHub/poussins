"""
Propositional logic example using poussins DSL.
"""

from poussins import Lemma, Prop, Environment

a, b, c = Prop("A"), Prop("B"), Prop("C")

hilbert_s = Lemma("HilbertS", (a >> (b >> c)) >> ((a >> b) >> (a >> c)))
print(f"{hilbert_s.name}: {hilbert_s.statement}")

hilbert_s.intros(["habc", "hab", "ha"])
hilbert_s.apply("habc")
hilbert_s.exact("ha")
hilbert_s.apply("hab")
hilbert_s.exact("ha")
hilbert_s.qed(Environment())
print(f"Assignment: {hilbert_s.assignment}")
