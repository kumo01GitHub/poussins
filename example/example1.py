"""
Propositional logic example using poussins DSL.
"""
from poussins import (
    Example, Prop, Environment,
    EVar, EConst, EApp, EPi, ESort, UnivLevelZero,
    ConstantDeclaration, InductiveDeclaration, ConstructorDeclaration
)


env = Environment()

prop_sort = ESort(UnivLevelZero())

and_type = EPi(
    var="A", domain=prop_sort,
    body=EPi(var="B", domain=prop_sort, body=prop_sort)
)

env.add(InductiveDeclaration(
    name="And",
    level_params=(),
    type=and_type,
    constructor_names=("And.intro",)
))

and_intro_type = EPi(
    var="A", domain=prop_sort,
    body=EPi(
        var="B", domain=prop_sort,
        body=EPi(
            var="_hA", domain=EVar("A"),
            body=EPi(
                var="_hB", domain=EVar("B"),
                body=EApp(EApp(EConst(name="And", levels=()), EVar("A")), EVar("B"))
            )
        )
    )
)

env.add(ConstructorDeclaration(
    name="And.intro",
    level_params=(),
    inductive_name="And",
    type=and_intro_type
))

env.add(ConstantDeclaration(name="P", level_params=(), type=prop_sort, value=EConst("P", ())))
env.add(ConstantDeclaration(name="Q", level_params=(), type=prop_sort, value=EConst("Q", ())))

p, q = Prop("P"), Prop("Q")

example = Example(p >> (q >> (p & q)), env)
print(f"Example: {example.statement}")

example.intro("hP")
example.intro("hQ")
example.constructor()
example.exact("hP")
example.exact("hQ")

example.qed()
print(f"Example has been successfully proved ✨:")
print(f"    {example.manager.current_proof_term}")
