"""
Propositional logic example using poussins DSL.
"""
from poussins import Example, Prop, Environment


env = Environment.default()

p, q = Prop("P", env), Prop("Q", env)

example = Example(p >> (q >> (p & q)), env)
print(f"Example: {example.statement}")

example.intros(["hP", "hQ"])
example.constructor()
example.exact("hP")
example.exact("hQ")

example.qed()
print(f"Example has been successfully proved ✨:")
print(f"    {example.manager.current_proof_term}")
