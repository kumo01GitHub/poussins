"""
Example proof that exercises the Nat DSL and the induction tactic.
"""
from poussins import Environment, Example, Prop
from poussins.ast import EApp, EConst, EVar
from poussins.framework.nat import Nat


env = Environment.default()

# Prove that equality is reflexive for an arbitrary natural number using tactics.
statement = Prop.forall(("n", Nat.type()), Nat.eq(Nat("n"), Nat("n")))
example = Example(statement.expr, env)
print(f"Example: {example.statement}")

example.intro("n")
example.induction("n")
example.exact(EApp(EApp(EConst("Eq.refl", ()), Nat.type()), EConst("Nat.zero", ())))
example.exact(EApp(EApp(EConst("Eq.refl", ()), Nat.type()), EApp(EConst("Nat.succ", ()), EVar("n1"))))

example.qed()
print("Example has been successfully proved ✨:")
print(f"    {example.manager.current_proof_term}")
