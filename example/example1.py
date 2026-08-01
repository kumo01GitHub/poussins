"""
Propositional logic example using poussins DSL.
"""
from poussins import Example, Prop, Environment


env = Environment.default()

p, q = Prop("P", env), Prop("Q", env)

example1 = Example(p >> (q >> (p & q)), env)
print(f"Example1: {example1.statement}")

example1.intros(["hP", "hQ"])
example1.constructor()
example1.exact("hP")
example1.exact("hQ")

example1.qed()
print(f"Example1 has been successfully proved ✨:")
print(f"    {example1.manager.current_proof_term}")


print()


example2 = Example(p >> p, env)
print(f"Example2: {example2.statement}")

example2.intro("hP")
example2.assumption()

example2.qed()
print(f"Example2 has been successfully proved ✨:")
print(f"    {example2.manager.current_proof_term}")
