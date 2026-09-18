"""
Main Pokémon Red Agent powered by TypeSafe AI's Jev System One model.
Combines RAM state extraction, Jev tactical decisions, and waypoint navigation.
"""

from __future__ import annotations

import logging
import time
from typing import Any, Dict

from ...core.base_agent import BaseAgent
from ...core.jev_client import JevDecisionClient
from ...core.telemetry import TelemetryTracker
from .navigator import OverworldNavigator
from .state import PokemonMemoryReader, PokemonRedState
from .tactics import CombatTactician

logger = logging.getLogger(__name__)


class PokemonRedAgent(BaseAgent):
    def __init__(
        self,
        client: JevDecisionClient,
        telemetry: TelemetryTracker,
        memory_reader: Any = None,
    ):
        super().__init__(client=client, telemetry=telemetry)
        self.reader = PokemonMemoryReader(memory_reader) if memory_reader else None
        self.tactician = CombatTactician()
        self.navigator = OverworldNavigator()
        self.in_menu_sequence: bool = False
        self.last_decision_time: float = 0.0

    def set_memory_reader(self, memory_reader: Any):
        self.reader = PokemonMemoryReader(memory_reader)

    def act(self, game_state: Any = None) -> str:
        """
        Executes one high-level tick of the agent:
        1. Reads game RAM state
        2. Routes to Combat (Jev System 1) or Dialogue or Overworld Navigation
        3. Returns the controller button to press ('A', 'B', 'UP', 'DOWN', etc.)
        """
        if not self.reader:
            return "A"

        state: PokemonRedState = self.reader.extract_state()

        # 1. Clear any active dialog/textbox
        if state.text_active:
            return "B" if time.time() % 2 == 0 else "A"

        # 2. Combat Encounter
        if state.is_in_battle:
            return self._handle_combat(state)

        # 3. Overworld Navigation
        return self.navigator.get_navigation_step(state)

    def step(self) -> str:
        return self.act()

    def _handle_combat(self, state: PokemonRedState) -> str:
        """Processes an in-battle turn using Jev System 1 decisions."""
        now = time.time()
        # Rate-limit queries per second so we don't spam during transition frames
        if now - self.last_decision_time < 0.2:
            return "A"

        self.last_decision_time = now
        jev_state = state.to_jev_dict()
        questions = self.tactician.build_combat_questions(state)

        try:
            resp = self.client.decide(state=jev_state, questions=questions)
            action, details = self.tactician.interpret_decision(resp.answers)

            logger.info(
                f"[Jev System 1] Action: {action} | Move: {details['move']} | "
                f"Heal: {details['should_heal']} | Wipe Risk: {details['risk_level']}"
            )

            # Map combat action to menu inputs
            if action == "fight":
                # In Gen 1, Fight is top-left option (A button)
                return "A"
            elif action == "item":
                return "DOWN"  # Move down to items
            elif action == "run":
                return "DOWN"  # Move to run
            elif action == "switch":
                return "RIGHT"  # Move to PKMN switch

            return "A"

        except Exception as e:
            logger.error(f"Error getting Jev decision: {e}", exc_info=True)
            return "A"
