from jev_plays.core.jev_client import JevDecisionClient
from jev_plays.core.telemetry import TelemetryTracker
from jev_plays.games.pokemon_red.agent import PokemonRedAgent
from jev_plays.games.pokemon_red import ram_map


class MockMemory:
    def __init__(self):
        self.data = bytearray(0x10000)

    def __getitem__(self, idx):
        return self.data[idx]

    def __setitem__(self, idx, val):
        self.data[idx] = val


def test_agent_dialogue_handling():
    mem = MockMemory()
    mem[ram_map.ADDR_TEXT_BOX_OPEN] = 1

    telemetry = TelemetryTracker()
    client = JevDecisionClient(telemetry=telemetry, mock_mode=True)
    agent = PokemonRedAgent(client=client, telemetry=telemetry, memory_reader=mem)

    action = agent.step()
    assert action in ["A", "B"]


def test_agent_battle_step():
    mem = MockMemory()
    mem[ram_map.ADDR_BATTLE_TYPE] = 1  # Wild battle
    mem[ram_map.ADDR_BATTLE_MON_SPECIES] = 0xB0  # Charmander
    mem[ram_map.ADDR_BATTLE_MON_LEVEL] = 5
    mem[ram_map.ADDR_BATTLE_MON_HP] = 0
    mem[ram_map.ADDR_BATTLE_MON_HP + 1] = 20
    mem[ram_map.ADDR_BATTLE_MON_MAX_HP] = 0
    mem[ram_map.ADDR_BATTLE_MON_MAX_HP + 1] = 20
    mem[ram_map.ADDR_BATTLE_MON_MOVES] = 10  # Scratch
    mem[ram_map.ADDR_ENEMY_MON_SPECIES] = 0x54  # Pidgey
    mem[ram_map.ADDR_ENEMY_MON_LEVEL] = 3
    mem[ram_map.ADDR_ENEMY_MON_HP] = 0
    mem[ram_map.ADDR_ENEMY_MON_HP + 1] = 12
    mem[ram_map.ADDR_ENEMY_MON_MAX_HP] = 0
    mem[ram_map.ADDR_ENEMY_MON_MAX_HP + 1] = 12

    telemetry = TelemetryTracker()
    client = JevDecisionClient(telemetry=telemetry, mock_mode=True)
    agent = PokemonRedAgent(client=client, telemetry=telemetry, memory_reader=mem)

    action = agent.step()
    # In combat, agent should output a valid menu action ('A', 'DOWN', 'RIGHT')
    assert action in ["A", "DOWN", "RIGHT"]
    assert telemetry.total_calls >= 1
