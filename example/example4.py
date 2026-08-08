"""
Propositional logic example using poussins DSL.
"""
from poussins.environment import Environment
from poussins.framework import Example, Prop


env = Environment.standard()

example = Example(Prop.bottom() >> Prop("A", env), env)
print(f"Example: {example.statement}")

example.intro("hFalse")
example.exfalso()
example.exact("hFalse")

example.qed()
print("Example has been successfully proved ✨:")
print(f"    {example.manager.current_proof_term}")
