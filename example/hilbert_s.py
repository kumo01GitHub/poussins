"""Example of a proof of the Hilbert S axiom in Poussins."""
from poussins.framework import Lemma, Prop, create_standard_environment

env = create_standard_environment()

p, q, r = Prop("P"), Prop("Q"), Prop("R")
statement = Prop.forall(
    (p, q, r),
    (p >> (q >> r)) >> ((p >> q) >> (p >> r)),
)
hilbert_s = Lemma("HilbertS", statement, env)

hilbert_s.intros(["P", "Q", "R", "hPQR", "hPQ", "hP"])
hilbert_s.apply("hPQR")
hilbert_s.exact("hP")
hilbert_s.apply("hPQ")
hilbert_s.exact("hP")

hilbert_s.qed()
