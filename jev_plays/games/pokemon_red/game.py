"""
PyBoy Game Boy emulator wrapper for Pokémon Red.
"""

from __future__ import annotations

import logging
from pathlib import Path
from typing import Any, Dict, Optional

from pyboy import PyBoy

from ...core.base_game import BaseGame
from .state import PokemonMemoryReader, PokemonRedState

logger = logging.getLogger(__name__)


class PokemonRedGame(BaseGame):
    def __init__(
        self,
        rom_path: str | Path,
        headless: bool = False,
        emulation_speed: int = 0,
        sound: bool = False,
    ):
        self.rom_path = Path(rom_path)
        if not self.rom_path.exists():
            raise FileNotFoundError(f"Pokemon Red ROM not found at: {self.rom_path.resolve()}")

        window_type = "null" if headless else "SDL2"
        logger.info(f"Launching PyBoy with ROM: {self.rom_path} (Window: {window_type}, Speed: {emulation_speed}x)")

        self.pyboy = PyBoy(
            str(self.rom_path),
            window=window_type,
            sound=sound,
        )
        self.pyboy.set_emulation_speed(emulation_speed)
        self.reader = PokemonMemoryReader(self.pyboy.memory)

    def reset(self) -> Dict[str, Any]:
        """Ticks initial frames past Game Boy boot sequence."""
        for _ in range(120):
            self.pyboy.tick()
        return self.get_state()

    def step(self, action: str) -> Dict[str, Any]:
        """
        Sends button press into PyBoy emulator and advances frames.
        Valid actions: 'A', 'B', 'START', 'SELECT', 'UP', 'DOWN', 'LEFT', 'RIGHT', 'PASS'
        """
        action = action.upper()
        button_map = {
            "A": "a",
            "B": "b",
            "START": "start",
            "SELECT": "select",
            "UP": "up",
            "DOWN": "down",
            "LEFT": "left",
            "RIGHT": "right",
        }

        if action in button_map:
            btn = button_map[action]
            self.pyboy.button_press(btn)
            # Hold button for 8 frames
            for _ in range(8):
                self.pyboy.tick()
            self.pyboy.button_release(btn)
            # Release delay for 8 frames
            for _ in range(8):
                self.pyboy.tick()
        else:
            # Idle tick
            for _ in range(16):
                self.pyboy.tick()

        return self.get_state()

    def get_state(self) -> Dict[str, Any]:
        parsed: PokemonRedState = self.reader.extract_state()
        return parsed.to_jev_dict()

    def is_done(self) -> bool:
        # Hall of Fame map ID is 0x76
        parsed: PokemonRedState = self.reader.extract_state()
        return parsed.overworld.is_hall_of_fame

    def close(self) -> None:
        if self.pyboy:
            self.pyboy.stop()
