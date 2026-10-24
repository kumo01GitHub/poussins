"""Example 9: Practical demonstration of quotient types using apply."""
from poussins.ast import (
    EConst,
    app,
    lam,
)
from poussins.framework import (
    Definition,
    Example,
    Prop,
    Quot,
    create_standard_environment,
)
from poussins.framework.inductive_types import Nat

env = create_standard_environment()

nat_type = Nat.type_expr()
eq_const = EConst("Eq", (Nat.sort().level,))

rel_type = Prop.forall((Nat("x"), Nat("y")), Prop.sort())
rel_expr = lam(
    (Nat("x").to_binding(), Nat("y").to_binding()),
    Nat.eq(Nat("x") % Nat(3), Nat("y") % Nat(3)),
)

rel_def = Definition(env, "NMod3", rel_type.statement, rel_expr)
rel_def.declare()

q_one = Quot[rel_def](Nat(1))
q_four = Quot[rel_def](Nat(4))

example = Example(app(eq_const, Quot[rel_def].type_expr(), q_one.value, q_four.value), env)
example.apply(Quot[rel_def].sound(Nat(1), Nat(4)))
example.rfl()
example.qed()
