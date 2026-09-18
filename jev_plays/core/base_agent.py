"""
Base interface for game-playing agents powered by Jev.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any, Dict

from .jev_client import JevDecisionClient
from .telemetry import TelemetryTracker


class BaseAgent(ABC):
    def __init__(self, client: JevDecisionClient, telemetry: TelemetryTracker):
        self.client = client
        self.telemetry = telemetry

    @abstractmethod
    def act(self, game_state: Dict[str, Any]) -> str:
        """Determines the next controller action based on game state and Jev decisions."""
        pass
