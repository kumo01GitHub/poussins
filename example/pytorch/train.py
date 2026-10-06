"""Training script for learning tactic policies from proof corpora."""
from __future__ import annotations

from pathlib import Path

from poussins.integration.pytorch import (
    ProofCorpus,
    ProofDataset,
    TacticPredictor,
    TacticTrainer,
)


def main() -> None:
    """Train neural tactic prediction model on proof corpus and persist checkpoint."""
    base_dir = Path(__file__).resolve().parent
    corpus_path = base_dir / "data" / "proof_corpus.json"
    checkpoint_path = base_dir / "models" / "tactic_model.pt"

    print(f"Loading corpus from: {corpus_path}")
    corpus = ProofCorpus.load_json(corpus_path)
    print(f"Loaded {len(corpus.steps)} proof steps.")

    vocab = corpus.build_vocabulary()
    print(f"Built vocabulary with {len(vocab.token_to_id)} tokens.")

    dataset = ProofDataset(corpus, vocab)
    model = TacticPredictor(
        vocab_size=len(vocab.token_to_id),
        embed_dim=64,
        hidden_dim=128,
        num_layers=2,
    )

    trainer = TacticTrainer(model, vocab, lr=5e-3)
    print("Training tactic model...")
    history = trainer.train(dataset, epochs=60, batch_size=8)

    final_loss = history["loss"][-1]
    final_acc = history["accuracy"][-1]
    print(
        f"Training completed. Final loss: {final_loss:.4f}, "
        f"Accuracy: {final_acc * 100:.1f}%"
    )

    trainer.save_checkpoint(checkpoint_path)
    print(f"Checkpoint successfully saved to: {checkpoint_path}")


if __name__ == "__main__":
    main()
