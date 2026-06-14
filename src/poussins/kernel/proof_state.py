"""
Kernel-level components of the proof system, including the core data structures and proof engine. 
"""
from __future__ import annotations
from collections import deque
from dataclasses import dataclass, field
from typing import Optional

from .goal import Goal


@dataclass
class ProofState:
    goals: deque[Goal] = field(default_factory=deque)

    @property
    def current_goal(self) -> Optional[Goal]:
        return self.goals[0] if self.goals else None

    @property
    def is_closed(self) -> bool:
        return not self.goals
