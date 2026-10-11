"""Example 7: Basic usage examples of 'have', 'specialize', and 'suffices' tactics."""
from poussins.framework import Example, Prop, create_standard_environment

env = create_standard_environment()
p, q, r = Prop("P"), Prop("Q"), Prop("R")
transitivity = Prop.forall(
    (("P", p.type()), ("Q", q.type()), ("R", r.type())),
    ((p >> q) >> ((q >> r) >> (p >> r)))
)

example1 = Example(transitivity, env)
example1.intros(["P", "Q", "R", "hPQ", "hQR", "hP"])
example1.have("hQ", q)
example1.apply("hPQ")
example1.exact("hP")
example1.apply("hQR")
example1.exact("hQ")
example1.qed()

example2 = Example(transitivity, env)
example2.intros(["P", "Q", "R", "hPQ", "hQR", "hP"])
example2.specialize("hPQ", "hP")
example2.apply("hQR")
example2.exact("hPQ")
example2.qed()

example3 = Example(transitivity, env)
example3.intros(["P", "Q", "R", "hPQ", "hQR", "hP"])
example3.suffices("hQ", q)
example3.apply("hQR")
example3.exact("hQ")
example3.apply("hPQ")
example3.exact("hP")
example3.qed()
