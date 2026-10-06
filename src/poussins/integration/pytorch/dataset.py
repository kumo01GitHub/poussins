"""Dataset representations and serialization for training tactic models."""
from __future__ import annotations

import json
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from ...errors import PyTorchIntegrationError
from ..serializer import TacticPlanSerializer
from .model import TacticVocabulary

try:
    import torch
    from torch.utils.data import Dataset
except ImportError as err:
    msg = (
        "PyTorch is required for this module. "
        "Install with: pip install 'poussins[pytorch]'"
    )
    raise PyTorchIntegrationError(msg) from err


@dataclass
class ProofStep:
    """Represents a single goal state and the chosen tactic action."""

    goal_statement: str
    hypotheses: list[tuple[str, str]] = field(default_factory=list)
    tactic_name: str = ""
    tactic_args: dict[str, Any] = field(default_factory=dict)

    def to_tokens(self) -> list[str]:
        """Convert goal statement and hypotheses into an interleaved token sequence."""
        tokens: list[str] = [TacticVocabulary.goal_symbol]
        tokens.extend(TacticVocabulary.tokenize(self.goal_statement))
        for name, typ_str in self.hypotheses:
            tokens.append(TacticVocabulary.hyp_symbol)
            tokens.extend(TacticVocabulary.tokenize(f"{name} : {typ_str}"))
        return tokens

    def to_dict(self) -> dict[str, Any]:
        """Serialize proof step into a JSON-safe dictionary using serializer."""
        encoded_args = {
            key: TacticPlanSerializer.encode_arg(val)
            for key, val in self.tactic_args.items()
        }
        return {
            "goal_statement": self.goal_statement,
            "hypotheses": [list(h) for h in self.hypotheses],
            "tactic_name": self.tactic_name,
            "tactic_args": encoded_args,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> ProofStep:
        """Instantiate a ProofStep from a dictionary representation."""
        raw_args = data.get("tactic_args", {})
        decoded_args = {
            key: TacticPlanSerializer.decode_arg(val)
            for key, val in raw_args.items()
        }
        return cls(
            goal_statement=data.get("goal_statement", ""),
            hypotheses=[tuple(h) for h in data.get("hypotheses", [])],
            tactic_name=data.get("tactic_name", ""),
            tactic_args=decoded_args,
        )


@dataclass
class ProofCorpus:
    """Collection of proof steps used to build vocabulary and train models."""

    steps: list[ProofStep] = field(default_factory=list)

    def add_step(self, step: ProofStep) -> None:
        """Append a step to the corpus."""
        self.steps.append(step)

    def save_json(self, file_path: str | Path) -> None:
        """Save the corpus to a JSON file."""
        data = [step.to_dict() for step in self.steps]
        with open(file_path, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2, ensure_ascii=False)

    @classmethod
    def load_json(cls, file_path: str | Path) -> ProofCorpus:
        """Load corpus steps from a JSON file."""
        with open(file_path, encoding="utf-8") as f:
            data = json.load(f)
        return cls(steps=[ProofStep.from_dict(d) for d in data])

    def build_vocabulary(self) -> TacticVocabulary:
        """Construct a TacticVocabulary populated with all tokens from this corpus."""
        vocab = TacticVocabulary()
        for step in self.steps:
            if step.tactic_name:
                vocab.add_tactic(step.tactic_name)
            vocab.build_from_texts([step.goal_statement])
            for name, typ in step.hypotheses:
                vocab.build_from_texts([f"{name} : {typ}"])
        return vocab


class ProofDataset(Dataset):
    """PyTorch Dataset yielding encoded goal sequences and tactic/argument labels."""

    def __init__(
        self,
        corpus: ProofCorpus,
        vocabulary: TacticVocabulary,
        max_seq_len: int = 128,
        max_hypotheses: int = 16,
    ) -> None:
        """Initialize dataset with corpus steps and token vocabulary."""
        self.corpus = corpus
        self.vocabulary = vocabulary
        self.max_seq_len = max_seq_len
        self.max_hypotheses = max_hypotheses
        self.samples = self._prepare_samples()

    def _prepare_samples(self) -> list[tuple[torch.Tensor, int, int]]:
        samples: list[tuple[torch.Tensor, int, int]] = []
        for step in self.corpus.steps:
            if step.tactic_name not in self.vocabulary.tactic_to_id:
                continue

            tokens = step.to_tokens()
            input_ids = self.vocabulary.encode(tokens, max_len=self.max_seq_len)
            tactic_id = self.vocabulary.tactic_to_id[step.tactic_name]

            arg_target = 0
            target_arg = step.tactic_args.get("expr_or_name") or step.tactic_args.get(
                "hyp_name"
            )
            if isinstance(target_arg, str):
                for idx, (hyp_name, _) in enumerate(step.hypotheses):
                    if hyp_name == target_arg and idx < self.max_hypotheses:
                        arg_target = idx
                        break

            samples.append(
                (
                    torch.tensor(input_ids, dtype=torch.long),
                    tactic_id,
                    arg_target,
                )
            )
        return samples

    def __len__(self) -> int:
        """Return total number of dataset samples."""
        return len(self.samples)

    def __getitem__(self, idx: int) -> tuple[torch.Tensor, torch.Tensor, torch.Tensor]:
        """Return a single sample (input_ids, tactic_target, arg_target)."""
        input_ids, tactic_target, arg_target = self.samples[idx]
        return (
            input_ids,
            torch.tensor(tactic_target, dtype=torch.long),
            torch.tensor(arg_target, dtype=torch.long),
        )
