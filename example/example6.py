"""
Example proof that exercises the Nat DSL and the induction tactic.
"""
from poussins.environment import Environment
from poussins.framework import Example, Nat, Prop


env = Environment.default()

# Prove that equality is reflexive for an arbitrary natural number using tactics.
statement = Prop.forall(("n", Nat.type()), Nat.eq(Nat("n"), Nat("n")))
example = Example(statement, env)
print(f"Example: {example.statement}")

example.intro("n")
example.induction("n")
example.constructor()
example.constructor()

example.qed()
print("Example has been successfully proved ✨:")
print(f"    {example.manager.current_proof_term}")
