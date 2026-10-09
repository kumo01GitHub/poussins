"""Training pipeline and checkpointing for neural tactic models."""
from __future__ import annotations

from pathlib import Path
from typing import Any

import torch
from torch import nn
from torch.optim import AdamW
from torch.utils.data import DataLoader

from ...errors import PyTorchIntegrationError
from .dataset import ProofDataset
from .model import SUPPORTED_TACTICS, TacticPredictor, TacticVocabulary


class TacticTrainer:
    """Trains a TacticPredictor model and manages checkpoint persistence."""

    def __init__(
        self,
        model: TacticPredictor,
        vocabulary: TacticVocabulary,
        lr: float = 1e-3,
        weight_decay: float = 1e-4,
        device: str = "cpu",
    ):
        """Initialize trainer with neural model, vocabulary, and training device."""
        self.model = model.to(device)
        self.vocabulary = vocabulary
        self.device = device
        self.optimizer = AdamW(
            self.model.parameters(), lr=lr, weight_decay=weight_decay
        )
        self.tactic_criterion = nn.CrossEntropyLoss()
        self.arg_criterion = nn.CrossEntropyLoss()

    def train_epoch(self, dataloader: DataLoader) -> tuple[float, float]:
        """Execute one training epoch over the dataset.

        Returns:
            avg_loss: Average loss over batches.
            accuracy: Tactic classification accuracy.

        """
        self.model.train()
        total_loss = 0.0
        correct_tactics = 0
        total_samples = 0

        for raw_inputs, raw_tactic, raw_arg in dataloader:
            inputs = raw_inputs.to(self.device)
            tactic_target = raw_tactic.to(self.device)
            arg_target = raw_arg.to(self.device)

            self.optimizer.zero_grad()
            tactic_logits, arg_logits = self.model(inputs)

            loss_tactic = self.tactic_criterion(tactic_logits, tactic_target)
            loss_arg = self.arg_criterion(arg_logits, arg_target)
            loss = loss_tactic + 0.5 * loss_arg

            loss.backward()
            self.optimizer.step()

            total_loss += loss.item() * len(inputs)
            preds = tactic_logits.argmax(dim=-1)
            correct_tactics += (preds == tactic_target).sum().item()
            total_samples += len(inputs)

        avg_loss = total_loss / max(1, total_samples)
        accuracy = correct_tactics / max(1, total_samples)
        return avg_loss, accuracy

    def train(
        self,
        dataset: ProofDataset,
        epochs: int = 50,
        batch_size: int = 16,
    ) -> dict[str, list[float]]:
        """Run training across the designated number of epochs."""
        dataloader = DataLoader(dataset, batch_size=batch_size, shuffle=True)
        history: dict[str, list[float]] = {"loss": [], "accuracy": []}

        for _ in range(epochs):
            loss, acc = self.train_epoch(dataloader)
            history["loss"].append(loss)
            history["accuracy"].append(acc)

        return history

    def save_checkpoint(self, path: str | Path) -> None:
        """Serialize model weights, architecture parameters, and vocabulary to disk."""
        target_path = Path(path)
        target_path.parent.mkdir(parents=True, exist_ok=True)

        payload: dict[str, Any] = {
            "model_state_dict": self.model.state_dict(),
            "vocab_data": self.vocabulary.to_dict(),
            "model_config": {
                "vocab_size": self.model.vocab_size,
                "num_tactics": self.model.num_tactics,
                "max_hypotheses": self.model.max_hypotheses,
                "embed_dim": self.model.embed_dim,
                "hidden_dim": self.model.hidden_dim,
                "num_layers": getattr(self.model, "num_layers", 2),
            },
        }
        torch.save(payload, target_path)

    @classmethod
    def load_checkpoint(
        cls,
        path: str | Path,
        device: str = "cpu",
    ) -> tuple[TacticPredictor, TacticVocabulary]:
        """Restore model and vocabulary from a saved checkpoint."""
        target_path = Path(path)
        if not target_path.exists():
            raise PyTorchIntegrationError(f"Checkpoint not found at '{target_path}'.")

        data = torch.load(target_path, map_location=device, weights_only=False)
        vocab = TacticVocabulary.from_dict(data["vocab_data"])
        cfg = data["model_config"]

        model = TacticPredictor(
            vocab_size=cfg["vocab_size"],
            num_tactics=cfg.get("num_tactics", len(SUPPORTED_TACTICS)),
            max_hypotheses=cfg.get("max_hypotheses", 16),
            embed_dim=cfg.get("embed_dim", 64),
            hidden_dim=cfg.get("hidden_dim", 128),
            num_layers=cfg.get("num_layers", 2),
        )
        model.load_state_dict(data["model_state_dict"])
        model.to(device)
        model.eval()

        return model, vocab
