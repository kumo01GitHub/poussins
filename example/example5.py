"""Example 5: Propositional logic with And and Or introduction rules."""
from poussins.ast import EVar
from poussins.environment import Environment
from poussins.framework import Example, Prop

env = Environment.standard()
p, q, r = Prop("P", env), Prop("Q", env), Prop("R", env)


# ------------------------------------------------------------------
# Example 1:
#   Prove that from (P and (Q or R)),
#   we can derive P using And and Or introduction rules.
# ------------------------------------------------------------------
example1 = Example((p & (q | r)) >> p, env)

example1.intro("hAnd")
example1.cases("hAnd", patterns=(("And.intro", "hP", "hOr"),))
example1.cases("hOr", patterns=(("Or.inl", "hQ"), ("Or.inr", "hR")))
example1.exact("hP")
example1.exact("hP")

example1.qed()


# ------------------------------------------------------------------
# Example 2:
#   Prove that from (P and (Q or R)),
#   we can derive P using And and Or introduction rules with a different approach.
# ------------------------------------------------------------------
example2 = Example((p & (q | r)) >> p, env)

example2.intro("hAnd")
example2.rcases("hAnd", ("And.intro", "hP", ("Or.inl", "hQ")))
example2.exact("hP")

example1.qed()


# ------------------------------------------------------------------
# Example 3: Prove that P follows from (P and (Q or R)) using the 'obtain' tactic.
# ------------------------------------------------------------------
example3 = Example((p & p) >> p, env)

example3.intro("hAnd")
example3.obtain(("And.intro", "hP1", "hP2"), EVar("hAnd"))
example3.exact("hP1")

example3.qed()
