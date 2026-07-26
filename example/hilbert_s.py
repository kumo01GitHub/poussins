from poussins import (
    Lemma, Prop, Environment,
    ESort, EVar, UnivLevelZero,
    ConstantDeclaration
)


env = Environment()

prop_sort = ESort(UnivLevelZero())

env.add(ConstantDeclaration(name="P", level_params=(), type=prop_sort, value=EVar("P")))
env.add(ConstantDeclaration(name="Q", level_params=(), type=prop_sort, value=EVar("Q")))
env.add(ConstantDeclaration(name="R", level_params=(), type=prop_sort, value=EVar("R")))

p, q, r = Prop("P"), Prop("Q"), Prop("R")

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
