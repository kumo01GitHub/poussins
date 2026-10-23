"""Example 9: Practical demonstration of quotient types using apply."""
from poussins.ast import (
    EConst,
    ELam,
    EPi,
    build_app_chain,
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

rel_type = EPi(
    var="x",
    domain=nat_type,
    body=EPi(
        var="y",
        domain=nat_type,
        body=Prop.sort(),
    ),
)
rel_expr = ELam(
    var="x",
    domain=nat_type,
    body=ELam(
        var="y",
        domain=nat_type,
        body=build_app_chain(
            eq_const,
            nat_type,
            Nat.to_expr(Nat("x") % Nat(3)),
            Nat.to_expr(Nat("y") % Nat(3)),
        ),
    ),
)
rel_def = Definition(env, "NMod3", rel_type, rel_expr)
rel_def.declare()

one_expr = Nat.to_expr(Nat(1))
four_expr = Nat.to_expr(Nat(4))

q_one = Quot[rel_def](Nat(1))
q_four = Quot[rel_def](Nat(4))

quot_type = build_app_chain(
    EConst("Quot", (Nat.sort().level,)),
    nat_type,
    rel_def.value,
)

eq_refl_term = build_app_chain(
    EConst("Eq.refl", (Nat.sort().level,)),
    nat_type,
    Nat.to_expr(Nat.mod(Nat(1), Nat(3))),
)

example = Example(build_app_chain(eq_const, quot_type, q_one.value, q_four.value), env)
example.simpl()
sound_term = Quot[rel_def].sound(one_expr, four_expr, eq_refl_term)
example.exact(sound_term)
example.qed()
