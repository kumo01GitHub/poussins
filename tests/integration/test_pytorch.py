"""Unit and integration tests for PyTorch-based tactic planning."""
from __future__ import annotations

import tempfile
from pathlib import Path

import pytest
import torch

from poussins import Environment, Nat, Prop
from poussins.ast import EVar
from poussins.errors import PyTorchIntegrationError
from poussins.integration.pytorch import (
    AITacticPlanner,
    ProofCorpus,
    ProofDataset,
    ProofStep,
    PyTorchProofScript,
    TacticPredictor,
    TacticTrainer,
    TacticVocabulary,
)

EXPECTED_SEQ_LEN = 16
EXPECTED_EPOCHS = 5
EXPECTED_ID_STEPS = 2


def torch_tensor(ids: list[int]) -> torch.Tensor:
    """Create a 2D long tensor from an ID list."""
    return torch.tensor([ids], dtype=torch.long)


def test_tactic_vocabulary_encoding() -> None:
    """Test tokenization, token addition, and sequence padding."""
    vocab = TacticVocabulary()
    tokens = vocab.tokenize("(Π hP : P, (And P P))")
    assert "(" in tokens
    assert "Π" in tokens
    assert "And" in tokens

    vocab.build_from_texts(["(Π hP : P, (And P P))"])
    encoded = vocab.encode(tokens, max_len=EXPECTED_SEQ_LEN)
    assert len(encoded) == EXPECTED_SEQ_LEN
    assert encoded[0] == vocab.token_to_id["("]
    assert encoded[-1] == vocab.pad_id


def test_tactic_predictor_forward() -> None:
    """Verify forward pass shapes of TacticPredictor."""
    vocab = TacticVocabulary()
    model = TacticPredictor(
        vocab_size=len(vocab.token_to_id) + 10,
        embed_dim=32,
        hidden_dim=64,
        num_layers=1,
    )
    dummy_input = torch_tensor([vocab.goal_id, 1, 2, 0])
    tactic_logits, arg_logits = model(dummy_input)

    assert tactic_logits.shape == (1, model.num_tactics)
    assert arg_logits.shape == (1, model.max_hypotheses)


def test_trainer_and_checkpoint_persistence() -> None:
    """Verify training on a miniature corpus and saving/loading model weights."""
    corpus = ProofCorpus(
        steps=[
            ProofStep(
                goal_statement="(Π hP : P, P)",
                tactic_name="intro",
                tactic_args={"name": "hP"},
            ),
            ProofStep(
                goal_statement="P",
                hypotheses=[("hP", "P")],
                tactic_name="exact",
                tactic_args={"expr_or_name": "hP"},
            ),
        ]
    )
    vocab = corpus.build_vocabulary()
    dataset = ProofDataset(corpus, vocab)
    model = TacticPredictor(
        vocab_size=len(vocab.token_to_id),
        embed_dim=32,
        hidden_dim=32,
        num_layers=1,
    )
    trainer = TacticTrainer(model, vocab, lr=1e-2)
    history = trainer.train(dataset, epochs=EXPECTED_EPOCHS, batch_size=2)
    assert len(history["loss"]) == EXPECTED_EPOCHS

    with tempfile.TemporaryDirectory() as tmp_dir:
        ckpt_path = Path(tmp_dir) / "test_model.pt"
        trainer.save_checkpoint(ckpt_path)
        assert ckpt_path.exists()

        loaded_model, loaded_vocab = TacticTrainer.load_checkpoint(ckpt_path)
        assert loaded_model.vocab_size == model.vocab_size
        assert len(loaded_vocab.token_to_id) == len(vocab.token_to_id)


def test_ai_planner_plan_and_execution() -> None:
    """Verify end-to-end plan synthesis and verification using pretrained checkpoint."""
    model_path = (
        Path(__file__).resolve().parent.parent.parent
        / "example"
        / "pytorch"
        / "models"
        / "tactic_model.pt"
    )
    if not model_path.exists():
        pytest.skip("Pretrained model not found.")

    model, vocab = TacticTrainer.load_checkpoint(model_path)
    env = Environment.standard()
    planner = AITacticPlanner(model, vocab, env=env, max_depth=8, top_k=4)

    # Test 1: Identity
    p = Prop("P", env)
    id_statement = (p >> p).expr
    plan = planner.plan(id_statement, env=env)
    assert len(plan) == EXPECTED_ID_STEPS

    script = PyTorchProofScript(id_statement, env, name="test_thm_id")
    script.execute_plan(plan)
    decl = script.qed()
    assert decl.name == "test_thm_id"

    # Test 2: Nat zero equality
    zero_eq = Prop(Nat.eq(Nat.zero(), Nat.zero())).expr
    plan_zero = planner.plan(zero_eq, env=env)
    assert len(plan_zero) == 1
    assert plan_zero[0][0] == "rfl"


def test_proof_step_arbitrary_tactic_serialization() -> None:
    """Verify that ProofStep accurately round-trips arbitrary tactic arguments."""
    step = ProofStep(
        goal_statement="(And P Q)",
        hypotheses=[("hP", "P")],
        tactic_name="cases",
        tactic_args={
            "hyp_name": "hP",
            "patterns": (("Nat.zero",), ("Nat.succ", "n")),
            "expr_or_name": EVar("hP"),
            "unfolding": frozenset({"Nat.add"}),
        },
    )
    serialized = step.to_dict()
    restored = ProofStep.from_dict(serialized)

    assert restored.tactic_name == "cases"
    assert restored.tactic_args["hyp_name"] == "hP"
    assert restored.tactic_args["patterns"] == (
        ("Nat.zero",),
        ("Nat.succ", "n"),
    )
    assert restored.tactic_args["expr_or_name"] == EVar("hP")
    assert restored.tactic_args["unfolding"] == frozenset({"Nat.add"})


def test_pytorch_proof_script_error_cases() -> None:
    """Verify error handling on unclosed proofs or unknown tactics."""
    env = Environment.standard()
    p = Prop("P", env)
    script = PyTorchProofScript((p >> p).expr, env, name="fail_thm")

    with pytest.raises(PyTorchIntegrationError, match="Unknown tactic"):
        script.execute_plan([("invalid_tactic_xyz", {})])

    with pytest.raises(PyTorchIntegrationError, match="cannot be closed"):
        script.qed()
