"""Example 5: Propositional logic with And and Or introduction rules."""
from poussins import Example, Prop, create_standard_environment
from poussins.ast import EVar

env = create_standard_environment()
p, q, r = Prop("P"), Prop("Q"), Prop("R")
bindings = (("P", p.type()), ("Q", q.type()), ("R", r.type()))


# ------------------------------------------------------------------
# Example 1:
#   Prove that from (P and (Q or R)),
#   we can derive P using And and Or introduction rules.
# ------------------------------------------------------------------
example1 = Example(Prop.forall(bindings, (p & (q | r)) >> p), env)

example1.intros(["P", "Q", "R"])
example1.intro("hAnd")
example1.cases("hAnd", with_=(("And.intro", "hP", "hOr"),))
example1.cases("hOr", with_=(("Or.inl", "hQ"), ("Or.inr", "hR")))
example1.exact("hP")
example1.exact("hP")

example1.qed()


# ------------------------------------------------------------------
# Example 2:
#   Prove that from (P and (Q or R)),
#   we can derive P using And and Or introduction rules with a different approach.
# ------------------------------------------------------------------
example2 = Example(Prop.forall(bindings, (p & (q | r)) >> p), env)

example2.intros(["P", "Q", "R"])
example2.intro("hAnd")
example2.rcases("hAnd", ("And.intro", "hP", ("Or.inl", "hQ")))
example2.exact("hP")
example2.exact("hP")

example2.qed()


# ------------------------------------------------------------------
# Example 3:
#   Prove that P follows from (P and (Q or R)) using the 'obtain' tactic.
# ------------------------------------------------------------------
example3 = Example(Prop.forall(bindings, (p & p) >> p), env)

example3.intros(["P", "Q", "R"])
example3.intro("hAnd")
example3.obtain(("And.intro", "hP1", "hP2"), EVar("hAnd"))
example3.exact("hP1")

example3.qed()
