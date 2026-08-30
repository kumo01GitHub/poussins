from poussins.environment import Environment
from poussins.framework import Lemma, Prop

env = Environment.standard()

p, q, r = Prop("P", env), Prop("Q", env), Prop("R", env)

hilbert_s = Lemma("HilbertS", ((p >> (q >> r)) >> ((p >> q) >> (p >> r))), env)

hilbert_s.intros(["hPQR", "hPQ", "hP"])
hilbert_s.apply("hPQR")
hilbert_s.exact("hP")
hilbert_s.apply("hPQ")
hilbert_s.exact("hP")

hilbert_s.qed()
