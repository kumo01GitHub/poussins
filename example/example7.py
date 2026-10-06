"""Example 7: Basic usage examples of 'have', 'specialize', and 'suffices' tactics."""
from poussins.environment import Environment
from poussins.framework import Example, Prop

env = Environment.standard()
p, q, r = Prop("P", env), Prop("Q", env), Prop("R", env)
transitivity = (p >> q) >> ((q >> r) >> (p >> r))

example1 = Example(transitivity, env)
example1.intros(["hPQ", "hQR", "hP"])
example1.have("hQ", "Q")
example1.apply("hPQ")
example1.exact("hP")
example1.apply("hQR")
example1.exact("hQ")
example1.qed()

example2 = Example(transitivity, env)
example2.intros(["hPQ", "hQR", "hP"])
example2.specialize("hPQ", "hP")
example2.apply("hQR")
example2.exact("hPQ")
example2.qed()

example3 = Example(transitivity, env)
example3.intros(["hPQ", "hQR", "hP"])
example3.suffices("hQ", "Q")
example3.apply("hQR")
example3.exact("hQ")
example3.apply("hPQ")
example3.exact("hP")
example3.qed()
