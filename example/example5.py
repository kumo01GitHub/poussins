"""Example proof that exercises the richer cases tactic API with nested And/Or branching.
"""
from poussins.environment import Environment
from poussins.framework import Example, Prop

env = Environment.standard()
p, q, r = Prop("P", env), Prop("Q", env), Prop("R", env)

example = Example((p & (q | r)) >> p, env)

example.intro("hAnd")
example.cases("hAnd", patterns=(("And.intro", "hP", "hOr"),))
example.cases("hOr", patterns=(("Or.inl", "hQ"), ("Or.inr", "hR")))
example.exact("hP")
example.exact("hP")

example.qed()
