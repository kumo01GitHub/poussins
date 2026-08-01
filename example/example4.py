"""
Propositional logic example using poussins DSL.
"""
from poussins import Example, Prop, Environment


env = Environment.default()

example = Example(Prop.bottom() >> Prop("A", env), env)
print(f"Example: {example.statement}")

example.intro("hFalse")
example.exfalso()
example.exact("hFalse")

example.qed()
print(f"Example has been successfully proved ✨:")
print(f"    {example.manager.current_proof_term}")
