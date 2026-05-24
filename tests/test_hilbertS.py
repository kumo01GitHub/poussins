"""
test_hilbertS.py: Minimal test for Hilbert-style proof closure using Theorem and tactics.
"""
from poussins.dsl.prop import Prop
from poussins.dsl.theorem import Theorem

def test_hilbertS_close():
    A = Prop("A")
    B = Prop("B")
    C = Prop("C")
    S = (A >> (B >> C)) >> ((A >> B) >> (A >> C))
    th = Theorem("hilbertS", S)

    def log_state(msg):
        current_goal = th.engine.state.current_goal()
        print(f"\n--- {msg} ---")
        print("Current goal:", current_goal)
        print("Goals stack:", list(th.engine.state.goals))
        print("Assignment:\n", th.engine.goal.assignment)
        if current_goal is not None:
            print("[DEBUG] current_goal.context.hyps:", current_goal.context.hyps)

    log_state("initial state")

    th.intro("habc"); log_state("after intro habc")
    th.intro("hab"); log_state("after intro hab")
    th.intro("ha"); log_state("after intro ha")
    th.apply("habc"); log_state("after apply habc")
    th.exact("ha"); log_state("after exact ha")
    th.apply("hab"); log_state("after apply hab")
    th.exact("ha"); log_state("after exact ha")
    th.qed()

    assert th.is_closed(), "Hilbert S proof should be closed"
