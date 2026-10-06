"""Integration module for PyTorch-based AI proof automation."""
from ...errors import PyTorchIntegrationError

try:
    import torch  # noqa: F401
except ImportError as err:
    raise PyTorchIntegrationError(
        "PyTorch is required for this integration module. "
        "Install optional dependencies with 'pip install \"poussins[pytorch]\"' "
        "or 'uv sync --extra pytorch'."
    ) from err

from .dataset import ProofCorpus, ProofDataset, ProofStep
from .model import SUPPORTED_TACTICS, TacticPredictor, TacticVocabulary
from .planner import AITacticPlanner
from .proof_script import PyTorchProofScript
from .trainer import TacticTrainer

__all__ = [
    "SUPPORTED_TACTICS",
    "AITacticPlanner",
    "ProofCorpus",
    "ProofDataset",
    "ProofStep",
    "PyTorchProofScript",
    "TacticPredictor",
    "TacticTrainer",
    "TacticVocabulary",
]
