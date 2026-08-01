from poussins import Lemma, Prop, Environment


env = Environment.default()

p, q, r = Prop("P", env), Prop("Q", env), Prop("R", env)

hilbert_s = Lemma("HilbertS", ((p >> (q >> r)) >> ((p >> q) >> (p >> r))), env)
print(f"{hilbert_s.name}: {hilbert_s.statement}")

hilbert_s.intro("hPQR")
hilbert_s.intro("hPQ")
hilbert_s.intro("hP")
hilbert_s.apply("hPQR")
hilbert_s.exact("hP")
hilbert_s.apply("hPQ")
hilbert_s.exact("hP")

hilbert_s.qed()
print(f"Theorem '{hilbert_s.name}' has been successfully proved ✨:")
print(f"    {hilbert_s.manager.current_proof_term}")
