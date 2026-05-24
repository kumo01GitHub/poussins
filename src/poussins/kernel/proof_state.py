""" 
"""

from __future__ import annotations
from collections import deque
from dataclasses import dataclass, field
from typing import Optional

from .goal import Goal


@dataclass
class ProofState:
    goals: deque[Goal] = field(default_factory=deque)
    
    def current_goal(self) -> Optional[Goal]:
        return self.goals[0] if self.goals else None
    
    def is_closed(self) -> bool:
        return not self.goals
