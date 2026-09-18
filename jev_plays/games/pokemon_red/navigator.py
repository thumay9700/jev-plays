"""
Overworld navigator and waypoint manager for Pokémon Red.
Directs high-level progression across Kanto and prevents wandering loops.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import List, Optional, Tuple
from .state import PokemonRedState


@dataclass
class Waypoint:
    name: str
    target_map_id: int
    target_x: int
    target_y: int
    description: str


class OverworldNavigator:
    """Manages progression checkpoints and movement directives."""

    def __init__(self):
        # High-level route waypoints
        self.waypoints: List[Waypoint] = [
            Waypoint("Oak's Lab", target_map_id=0x28, target_x=5, target_y=3, description="Get Starter Pokémon"),
            Waypoint("Route 1 North", target_map_id=0x0C, target_x=10, target_y=0, description="Walk to Viridian City"),
            Waypoint("Viridian Mart", target_map_id=0x1D, target_x=3, target_y=5, description="Pick up Oak's Parcel"),
            Waypoint("Return to Oak", target_map_id=0x28, target_x=5, target_y=2, description="Deliver Parcel & get Pokedex"),
            Waypoint("Viridian Forest Entry", target_map_id=0x0D, target_x=3, target_y=43, description="Enter Viridian Forest"),
            Waypoint("Viridian Forest Exit", target_map_id=0x33, target_x=1, target_y=0, description="Exit to Route 2 North"),
            Waypoint("Pewter Gym", target_map_id=0x36, target_x=4, target_y=3, description="Defeat Brock (Boulder Badge)"),
            Waypoint("Mt Moon 1F Entry", target_map_id=0x0E, target_x=54, target_y=5, description="Enter Mt. Moon"),
            Waypoint("Cerulean Gym", target_map_id=0x41, target_x=4, target_y=3, description="Defeat Misty (Cascade Badge)"),
        ]
        self.current_waypoint_index: int = 0

    @property
    def current_waypoint(self) -> Optional[Waypoint]:
        if self.current_waypoint_index < len(self.waypoints):
            return self.waypoints[self.current_waypoint_index]
        return None

    def get_navigation_step(self, state: PokemonRedState) -> str:
        """Determines the next directional input towards current target."""
        wp = self.current_waypoint
        if not wp:
            return "UP"

        # Check if arrived at map
        if state.overworld.map_id == wp.target_map_id:
            curr_x = state.overworld.x
            curr_y = state.overworld.y

            dx = wp.target_x - curr_x
            dy = wp.target_y - curr_y

            # Close enough to waypoint?
            if abs(dx) <= 1 and abs(dy) <= 1:
                self.current_waypoint_index += 1
                return "A"  # Trigger interaction

            # Move along largest delta first
            if abs(dx) > abs(dy):
                return "RIGHT" if dx > 0 else "LEFT"
            else:
                return "DOWN" if dy > 0 else "UP"

        # If not in target map, standard progression generally heads North or East in early game
        if state.overworld.map_id == 0x00:  # Pallet Town
            return "UP"
        elif state.overworld.map_id == 0x0C:  # Route 1
            return "UP"
        elif state.overworld.map_id == 0x01:  # Viridian City
            return "UP"
        elif state.overworld.map_id == 0x33:  # Viridian Forest
            return "UP"

        return "UP"
