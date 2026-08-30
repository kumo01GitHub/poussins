"""Kernel-level proof session management for handling proof states and their history."""
from __future__ import annotations

from ..errors import KernelStateError
from .proof_state import ProofState


class ProofSession:
    """Proof session that manages the immutable history of proof states."""

    def __init__(self, initial_state: ProofState):
        """Start a proof session from the given initial state."""
        self._history: list[ProofState] = [initial_state]

    @property
    def current_state(self) -> ProofState:
        """Return the current proof state (the last state in the history)."""
        return self._history[-1]

    @property
    def is_closed(self) -> bool:
        """Check if the proof session is closed (i.e., no active goals remain)."""
        return len(self.current_state.goals) == 0

    @property
    def history(self) -> tuple[ProofState, ...]:
        """Return an immutable tuple of the proof state history."""
        return tuple(self._history)

    def update_state(self, next_state: ProofState) -> None:
        """Update the proof session with a new state, appending it to the history."""
        self._history.append(next_state)

    def undo(self) -> None:
        """Undo the last proof state, reverting to the previous state in the history."""
        if len(self._history) > 1:
            _ = self._history.pop()
        else:
            raise KernelStateError("Cannot undo beyond the initial proof state.")
