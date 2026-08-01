"""
Propositional logic example using poussins DSL.
"""
from poussins import Example, Environment, Prop


env = Environment.default()

example1 = Example(Prop.top(), env)
print(f"Example1: {example1.statement}")

example1.constructor()

example1.qed()
print(f"Example1 has been successfully proved ✨:")
print(f"    {example1.manager.current_proof_term}")


example2 = Example(Prop.top(), env)
print(f"Example2: {example2.statement}")

example2.exact("True.intro")

example2.qed()
print(f"Example2 has been successfully proved ✨:")
print(f"    {example2.manager.current_proof_term}")
