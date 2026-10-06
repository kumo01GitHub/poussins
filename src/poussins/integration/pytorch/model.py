"""Neural network architectures and vocabulary handling for tactic prediction."""
from __future__ import annotations

import re
from dataclasses import dataclass, field
from typing import Any

import torch
from torch import nn
from torch.nn import functional

SUPPORTED_TACTICS: list[str] = [
    "intro",
    "intros",
    "exact",
    "apply",
    "rfl",
    "constructor",
    "assumption",
    "simpl",
]


@dataclass
class TacticVocabulary:
    """Manages token and tactic dictionaries for neural model encoding and decoding."""

    token_to_id: dict[str, int] = field(default_factory=dict)
    id_to_token: dict[int, str] = field(default_factory=dict)
    tactic_to_id: dict[str, int] = field(default_factory=dict)
    id_to_tactic: dict[int, str] = field(default_factory=dict)

    pad_symbol: str = "[PAD]"  # noqa: S105
    unk_symbol: str = "[UNK]"  # noqa: S105
    goal_symbol: str = "[GOAL]"  # noqa: S105
    hyp_symbol: str = "[HYP]"  # noqa: S105

    pad_id: int = 0
    unk_id: int = 1
    goal_id: int = 2
    hyp_id: int = 3

    def __post_init__(self) -> None:
        """Initialize default tokens and tactics if empty."""
        if not self.token_to_id:
            self._init_defaults()

    def _init_defaults(self) -> None:
        special_tokens = [
            self.pad_symbol,
            self.unk_symbol,
            self.goal_symbol,
            self.hyp_symbol,
        ]
        for idx, token in enumerate(special_tokens):
            self.token_to_id[token] = idx
            self.id_to_token[idx] = token

        for idx, tactic in enumerate(SUPPORTED_TACTICS):
            self.tactic_to_id[tactic] = idx
            self.id_to_tactic[idx] = tactic

    def add_tactic(self, tactic: str) -> int:
        """Add a tactic to the vocabulary if absent and return its id."""
        if tactic not in self.tactic_to_id:
            new_id = len(self.tactic_to_id)
            self.tactic_to_id[tactic] = new_id
            self.id_to_tactic[new_id] = tactic
            return new_id
        return self.tactic_to_id[tactic]

    @staticmethod
    def tokenize(text: str) -> list[str]:
        """Tokenize a proof statement or hypothesis string into syntactic tokens."""
        cleaned = re.sub(r"([()\[\],:])", r" \1 ", text)
        return [tok for tok in cleaned.split() if tok]

    def add_token(self, token: str) -> int:
        """Add a token to the vocabulary if absent and return its id."""
        if token not in self.token_to_id:
            new_id = len(self.token_to_id)
            self.token_to_id[token] = new_id
            self.id_to_token[new_id] = token
            return new_id
        return self.token_to_id[token]

    def build_from_texts(self, texts: list[str]) -> None:
        """Populate the token vocabulary from an iterable of raw text strings."""
        for text in texts:
            for token in self.tokenize(text):
                self.add_token(token)

    def encode(self, tokens: list[str], max_len: int = 128) -> list[int]:
        """Convert a list of string tokens into a padded list of token IDs."""
        ids = [self.token_to_id.get(tok, self.unk_id) for tok in tokens[:max_len]]
        if len(ids) < max_len:
            ids.extend([self.pad_id] * (max_len - len(ids)))
        return ids

    def to_dict(self) -> dict[str, Any]:
        """Serialize vocabulary mappings to a primitive dictionary."""
        return {
            "token_to_id": self.token_to_id,
            "id_to_token": {str(k): v for k, v in self.id_to_token.items()},
            "tactic_to_id": self.tactic_to_id,
            "id_to_tactic": {str(k): v for k, v in self.id_to_tactic.items()},
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> TacticVocabulary:
        """Deserialize vocabulary mappings from a dictionary."""
        vocab = cls()
        vocab.token_to_id = data["token_to_id"]
        vocab.id_to_token = {int(k): v for k, v in data["id_to_token"].items()}
        vocab.tactic_to_id = data["tactic_to_id"]
        vocab.id_to_tactic = {int(k): v for k, v in data["id_to_tactic"].items()}
        return vocab


class TacticPredictor(nn.Module):
    """Neural policy network for predicting tactics and hypothesis argument indices."""

    def __init__(  # noqa: PLR0913
        self,
        vocab_size: int,
        num_tactics: int = len(SUPPORTED_TACTICS),
        max_hypotheses: int = 16,
        embed_dim: int = 64,
        hidden_dim: int = 128,
        num_layers: int = 2,
    ) -> None:
        """Initialize the embedding, recurrent encoder, and prediction heads."""
        super().__init__()
        self.vocab_size = vocab_size
        self.num_tactics = num_tactics
        self.max_hypotheses = max_hypotheses
        self.embed_dim = embed_dim
        self.hidden_dim = hidden_dim
        self.num_layers = num_layers

        self.embedding = nn.Embedding(vocab_size, embed_dim, padding_idx=0)
        self.encoder = nn.GRU(
            input_size=embed_dim,
            hidden_size=hidden_dim,
            num_layers=num_layers,
            batch_first=True,
            bidirectional=True,
        )

        encoder_dim = hidden_dim * 2
        self.tactic_head = nn.Sequential(
            nn.Linear(encoder_dim, hidden_dim),
            nn.ReLU(),
            nn.Linear(hidden_dim, num_tactics),
        )

        self.arg_head = nn.Sequential(
            nn.Linear(encoder_dim, hidden_dim),
            nn.ReLU(),
            nn.Linear(hidden_dim, max_hypotheses),
        )

    def forward(
        self,
        input_ids: torch.Tensor,
    ) -> tuple[torch.Tensor, torch.Tensor]:
        """Perform a forward pass returning tactic and argument logits.

        Args:
            input_ids: Tensor of shape (batch_size, seq_len)

        Returns:
            tactic_logits: (batch_size, num_tactics)
            arg_logits: (batch_size, max_hypotheses)

        """
        embedded = self.embedding(input_ids)
        encoded, _ = self.encoder(embedded)

        mask = (input_ids != 0).unsqueeze(-1).float()
        sum_masked = (encoded * mask).sum(dim=1)
        lengths = mask.sum(dim=1).clamp(min=1.0)
        pooled = sum_masked / lengths

        tactic_logits = self.tactic_head(pooled)
        arg_logits = self.arg_head(pooled)

        return tactic_logits, arg_logits

    def predict_top_k(
        self,
        input_ids: torch.Tensor,
        top_k: int = 3,
    ) -> list[tuple[int, float]]:
        """Return the top-k predicted tactic IDs with softmax probabilities."""
        self.eval()
        with torch.no_grad():
            tactic_logits, _ = self.forward(input_ids)
            probs = functional.softmax(tactic_logits, dim=-1)[0]
            top_probs, top_indices = torch.topk(
                probs, min(top_k, self.num_tactics)
            )
            return [
                (int(idx.item()), float(prob.item()))
                for idx, prob in zip(top_indices, top_probs, strict=True)
            ]
