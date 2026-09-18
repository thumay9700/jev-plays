"""
Base interface for game environments and emulators.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any, Dict


class BaseGame(ABC):
    @abstractmethod
    def reset(self) -> Dict[str, Any]:
        """Resets or initializes the game state."""
        pass

    @abstractmethod
    def step(self, action: str) -> Dict[str, Any]:
        """Applies an input action (e.g. 'A', 'B', 'UP', 'START') and returns next state."""
        pass

    @abstractmethod
    def get_state(self) -> Dict[str, Any]:
        """Extracts structured state representation for Jev System One."""
        pass

    @abstractmethod
    def is_done(self) -> bool:
        """Returns True if game objective is completed or game is terminated."""
        pass

    @abstractmethod
    def close(self) -> None:
        """Cleans up emulator resources and windows."""
        pass
