"""Example 9: Practical demonstration of quotient types using apply."""
from poussins.ast import (
    EConst,
    ELam,
    EPi,
    build_app_chain,
)
from poussins.environment.library import QuotDeclaration
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
            Nat.to_expr(Nat.add(Nat("x"), Nat(3))),
            Nat.to_expr(Nat("y")),
        ),
    ),
)
rel_def = Definition(env, "my_rel", rel_type, rel_expr)
rel_def.declare()

one_expr = Nat.to_expr(Nat(1))
one_plus_three_expr = Nat.to_expr(Nat.add(Nat(1), Nat(3)))

q_one = Quot[rel_def](Nat(1))
q_target = Quot[rel_def](Nat.add(Nat(1), Nat(3)))

quot_type = build_app_chain(
    EConst("Quot", (Nat.sort().level,)),
    nat_type,
    rel_def.value,
)

statement = build_app_chain(eq_const, quot_type, q_one.value, q_target.value)

quot_sound_const = EConst(
    name=QuotDeclaration.QUOT_SOUND_DECLARATION.declaration.name,
    levels=(Nat.sort().level,),
)

example = Example(statement, env)
example.simpl()
example.apply(quot_sound_const)

eq_refl_term = build_app_chain(
    EConst("Eq.refl", (Nat.sort().level,)),
    nat_type,
    one_plus_three_expr,
)
example.exact(eq_refl_term)
example.qed()
