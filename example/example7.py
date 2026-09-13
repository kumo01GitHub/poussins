"""Basic usage examples of 'have', 'specialize', and 'suffices' tactics in Poussins."""

from poussins.environment import Environment
from poussins.framework import Example, Prop

env = Environment.standard()
p, q, r = Prop("P", env), Prop("Q", env), Prop("R", env)
transitivity = (p >> q) >> ((q >> r) >> (p >> r))

ex_have = Example(transitivity, env)
ex_have.intros(["hPQ", "hQR", "hP"])
ex_have.have("hQ", q.expr)
ex_have.apply("hPQ")
ex_have.exact("hP")
ex_have.apply("hQR")
ex_have.exact("hQ")
ex_have.qed()

ex_spec = Example(transitivity, env)
ex_spec.intros(["hPQ", "hQR", "hP"])
ex_spec.specialize("hPQ", "hP")
ex_spec.apply("hQR")
ex_spec.exact("hPQ")
ex_spec.qed()

ex_suff = Example(transitivity, env)
ex_suff.intros(["hPQ", "hQR", "hP"])
ex_suff.suffices("hQ", q.expr)
ex_suff.apply("hQR")
ex_suff.exact("hQ")
ex_suff.apply("hPQ")
ex_suff.exact("hP")
ex_suff.qed()
