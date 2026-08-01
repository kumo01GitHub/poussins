"""
Propositional logic examples using poussins DSL.
"""
from poussins import Example, Prop, Environment


env = Environment.default()
p, q = Prop("P", env), Prop("Q", env)


example1 = Example(p >> (p | q), env)
print(f"Example1: {example1.statement}")

example1.intro("hP")
example1.left()
example1.exact("hP")

example1.qed()
print("Example1 has been successfully proved ✨:")
print(f"    {example1.manager.current_proof_term}")


print()


example2 = Example(q >> (p | q), env)
print(f"Example2: {example2.statement}")

example2.intro("hQ")
example2.right()
example2.exact("hQ")

example2.qed()
print("Example2 has been successfully proved ✨:")
print(f"    {example2.manager.current_proof_term}")


print()


example3 = Example(p >> (q >> (p & q)), env)
print(f"Example3: {example3.statement}")

example3.intros(["hP", "hQ"])
example3.split()
example3.exact("hP")
example3.exact("hQ")

example3.qed()
print("Example3 has been successfully proved ✨:")
print(f"    {example3.manager.current_proof_term}")
