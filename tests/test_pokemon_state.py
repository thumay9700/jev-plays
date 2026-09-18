from jev_plays.games.pokemon_red.state import PokemonMemoryReader
from jev_plays.games.pokemon_red import ram_map


class MockMemory:
    def __init__(self):
        self.data = bytearray(0x10000)

    def __getitem__(self, idx):
        return self.data[idx]

    def __setitem__(self, idx, val):
        self.data[idx] = val


def test_overworld_state_extraction():
    mem = MockMemory()
    mem[ram_map.ADDR_BATTLE_TYPE] = 0
    mem[ram_map.ADDR_MAP_ID] = 0x00  # Pallet Town
    mem[ram_map.ADDR_X_COORD] = 5
    mem[ram_map.ADDR_Y_COORD] = 8
    mem[ram_map.ADDR_BADGES] = 0b00000011  # 2 badges
    mem[ram_map.ADDR_TEXT_BOX_OPEN] = 0

    reader = PokemonMemoryReader(mem)
    state = reader.extract_state()

    assert not state.is_in_battle
    assert state.overworld.map_name == "Pallet Town"
    assert state.overworld.x == 5
    assert state.overworld.y == 8
    assert not state.overworld.is_hall_of_fame

    jev_dict = state.to_jev_dict()
    assert jev_dict["in_battle"] is False
    assert jev_dict["location"] == "Pallet Town"
    assert jev_dict["badges_count"] == 2


def test_battle_state_extraction():
    mem = MockMemory()
    mem[ram_map.ADDR_BATTLE_TYPE] = 2  # Trainer battle
    mem[ram_map.ADDR_MAP_ID] = 0x36   # Pewter Gym

    # Player Pokemon (Charmander, Level 12, 30/30 HP)
    mem[ram_map.ADDR_BATTLE_MON_SPECIES] = 0xB0  # Charmander
    mem[ram_map.ADDR_BATTLE_MON_LEVEL] = 12
    mem[ram_map.ADDR_BATTLE_MON_HP] = 0
    mem[ram_map.ADDR_BATTLE_MON_HP + 1] = 30
    mem[ram_map.ADDR_BATTLE_MON_MAX_HP] = 0
    mem[ram_map.ADDR_BATTLE_MON_MAX_HP + 1] = 30
    mem[ram_map.ADDR_BATTLE_MON_TYPE1] = 0x14  # Fire
    mem[ram_map.ADDR_BATTLE_MON_TYPE2] = 0x14
    mem[ram_map.ADDR_BATTLE_MON_MOVES] = 10     # Scratch
    mem[ram_map.ADDR_BATTLE_MON_MOVES + 1] = 52 # Ember

    # Enemy Pokemon (Onix, Level 14, 40/40 HP)
    mem[ram_map.ADDR_ENEMY_MON_SPECIES] = 0x6E  # Onix
    mem[ram_map.ADDR_ENEMY_MON_LEVEL] = 14
    mem[ram_map.ADDR_ENEMY_MON_HP] = 0
    mem[ram_map.ADDR_ENEMY_MON_HP + 1] = 40
    mem[ram_map.ADDR_ENEMY_MON_MAX_HP] = 0
    mem[ram_map.ADDR_ENEMY_MON_MAX_HP + 1] = 40
    mem[ram_map.ADDR_ENEMY_MON_TYPE1] = 0x05    # Rock
    mem[ram_map.ADDR_ENEMY_MON_TYPE2] = 0x04    # Ground

    reader = PokemonMemoryReader(mem)
    state = reader.extract_state()

    assert state.is_in_battle
    assert state.battle.battle_type == "trainer"
    assert state.battle.player_mon.species == "Charmander"
    assert "Ember" in state.battle.player_mon.moves
    assert "Scratch" in state.battle.player_mon.moves
    assert state.battle.enemy_mon.species == "Onix"
    assert state.battle.enemy_mon.hp_percent == 1.0

    jev_dict = state.to_jev_dict()
    assert jev_dict["in_battle"] is True
    assert jev_dict["player_pokemon"]["species"] == "Charmander"
    assert jev_dict["opponent_pokemon"]["species"] == "Onix"
