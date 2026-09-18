"""
State extractor and data models for Pokémon Red.
Translates raw Game Boy RAM into clean Pydantic state dictionaries for Jev.
"""

from __future__ import annotations

from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field

from . import ram_map


class ActivePokemon(BaseModel):
    species: str
    level: int
    current_hp: int
    max_hp: int
    hp_percent: float
    types: List[str]
    moves: List[str]
    status: str


class BattleState(BaseModel):
    in_battle: bool
    battle_type: str  # "none", "wild", "trainer"
    player_mon: Optional[ActivePokemon] = None
    enemy_mon: Optional[ActivePokemon] = None
    has_healing_items: bool = True


class OverworldState(BaseModel):
    map_id: int
    map_name: str
    x: int
    y: int
    badges: int
    is_hall_of_fame: bool


class PokemonRedState(BaseModel):
    is_in_battle: bool
    battle: BattleState
    overworld: OverworldState
    text_active: bool

    def to_jev_dict(self) -> Dict[str, Any]:
        """Convert state into a dense, token-efficient dictionary for Jev System One."""
        if self.is_in_battle and self.battle.player_mon and self.battle.enemy_mon:
            return {
                "in_battle": True,
                "battle_type": self.battle.battle_type,
                "player_pokemon": {
                    "species": self.battle.player_mon.species,
                    "level": self.battle.player_mon.level,
                    "hp_percent": round(self.battle.player_mon.hp_percent, 2),
                    "types": self.battle.player_mon.types,
                    "moves": self.battle.player_mon.moves,
                    "status": self.battle.player_mon.status,
                },
                "opponent_pokemon": {
                    "species": self.battle.enemy_mon.species,
                    "level": self.battle.enemy_mon.level,
                    "hp_percent": round(self.battle.enemy_mon.hp_percent, 2),
                    "types": self.battle.enemy_mon.types,
                },
                "has_healing_items": self.battle.has_healing_items,
            }
        else:
            return {
                "in_battle": False,
                "location": self.overworld.map_name,
                "coords": [self.overworld.x, self.overworld.y],
                "badges_count": bin(self.overworld.badges).count("1"),
                "text_active": self.text_active,
            }


class PokemonMemoryReader:
    """Reads structured state from PyBoy memory interface."""

    def __init__(self, memory_reader):
        self.mem = memory_reader

    def read_word_be(self, addr: int) -> int:
        return (self.mem[addr] << 8) | self.mem[addr + 1]

    def read_moves(self, addr: int) -> List[str]:
        moves = []
        for i in range(4):
            move_id = self.mem[addr + i]
            if move_id in ram_map.MOVES:
                moves.append(ram_map.MOVES[move_id])
            elif move_id != 0:
                moves.append(f"Move_{move_id}")
        return moves if moves else ["Tackle"]

    def read_types(self, addr1: int, addr2: int) -> List[str]:
        t1 = ram_map.TYPES.get(self.mem[addr1], "Normal")
        t2 = ram_map.TYPES.get(self.mem[addr2], "Normal")
        return [t1] if t1 == t2 else [t1, t2]

    def extract_state(self) -> PokemonRedState:
        raw_b_type = self.mem[ram_map.ADDR_BATTLE_TYPE]
        in_battle = raw_b_type in (1, 2)
        b_type_str = "wild" if raw_b_type == 1 else ("trainer" if raw_b_type == 2 else "none")

        player_mon = None
        enemy_mon = None

        if in_battle:
            # Player active mon
            p_hp = self.read_word_be(ram_map.ADDR_BATTLE_MON_HP)
            p_max_hp = max(1, self.read_word_be(ram_map.ADDR_BATTLE_MON_MAX_HP))
            p_species_id = self.mem[ram_map.ADDR_BATTLE_MON_SPECIES]
            p_species = ram_map.SPECIES.get(p_species_id, f"Mon_{p_species_id}")
            p_level = self.mem[ram_map.ADDR_BATTLE_MON_LEVEL]
            p_types = self.read_types(ram_map.ADDR_BATTLE_MON_TYPE1, ram_map.ADDR_BATTLE_MON_TYPE2)
            p_moves = self.read_moves(ram_map.ADDR_BATTLE_MON_MOVES)

            player_mon = ActivePokemon(
                species=p_species,
                level=p_level,
                current_hp=p_hp,
                max_hp=p_max_hp,
                hp_percent=min(1.0, max(0.0, p_hp / p_max_hp)),
                types=p_types,
                moves=p_moves,
                status="normal" if self.mem[ram_map.ADDR_BATTLE_MON_STATUS] == 0 else "statused",
            )

            # Enemy active mon
            e_hp = self.read_word_be(ram_map.ADDR_ENEMY_MON_HP)
            e_max_hp = max(1, self.read_word_be(ram_map.ADDR_ENEMY_MON_MAX_HP))
            e_species_id = self.mem[ram_map.ADDR_ENEMY_MON_SPECIES]
            e_species = ram_map.SPECIES.get(e_species_id, f"Mon_{e_species_id}")
            e_level = self.mem[ram_map.ADDR_ENEMY_MON_LEVEL]
            e_types = self.read_types(ram_map.ADDR_ENEMY_MON_TYPE1, ram_map.ADDR_ENEMY_MON_TYPE2)

            enemy_mon = ActivePokemon(
                species=e_species,
                level=e_level,
                current_hp=e_hp,
                max_hp=e_max_hp,
                hp_percent=min(1.0, max(0.0, e_hp / e_max_hp)),
                types=e_types,
                moves=["Attack"],
                status="normal" if self.mem[ram_map.ADDR_ENEMY_MON_STATUS] == 0 else "statused",
            )

        map_id = self.mem[ram_map.ADDR_MAP_ID]
        map_name = ram_map.MAPS.get(map_id, f"Map_{hex(map_id)}")
        x = self.mem[ram_map.ADDR_X_COORD]
        y = self.mem[ram_map.ADDR_Y_COORD]
        badges = self.mem[ram_map.ADDR_BADGES]
        text_active = self.mem[ram_map.ADDR_TEXT_BOX_OPEN] != 0

        battle_state = BattleState(
            in_battle=in_battle,
            battle_type=b_type_str,
            player_mon=player_mon,
            enemy_mon=enemy_mon,
            has_healing_items=True,
        )

        overworld_state = OverworldState(
            map_id=map_id,
            map_name=map_name,
            x=x,
            y=y,
            badges=badges,
            is_hall_of_fame=(map_id == 0x76),
        )

        return PokemonRedState(
            is_in_battle=in_battle,
            battle=battle_state,
            overworld=overworld_state,
            text_active=text_active,
        )
