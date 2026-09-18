"""
RAM offsets and constant tables for Pokémon Red / Blue (US Version).
"""

# RAM Addresses
ADDR_BATTLE_TYPE = 0xD057       # 0 = not in battle, 1 = wild, 2 = trainer, 0xFF = lost
ADDR_BATTLE_TURN = 0xD05C       # Battle sub-turn/phase
ADDR_MAP_ID = 0xD35E            # Current map identifier (Pallet Town = 0, Viridian = 1, etc.)
ADDR_X_COORD = 0xD362           # Player X coordinate on map
ADDR_Y_COORD = 0xD361           # Player Y coordinate on map
ADDR_BADGES = 0xD356            # Bitmask of obtained gym badges (Boulder, Cascade, Thunder, Rainbow...)
ADDR_PARTY_COUNT = 0xD163       # Number of Pokémon in party (1-6)

# Active Battle Memory (Player)
ADDR_BATTLE_MON_SPECIES = 0xD014
ADDR_BATTLE_MON_HP = 0xD015      # 2 bytes big-endian
ADDR_BATTLE_MON_STATUS = 0xD018  # 0 = normal, bits for sleep, poison, burn, freeze, paralyze
ADDR_BATTLE_MON_TYPE1 = 0xD019
ADDR_BATTLE_MON_TYPE2 = 0xD01A
ADDR_BATTLE_MON_MOVES = 0xD01C   # 4 bytes
ADDR_BATTLE_MON_LEVEL = 0xD022
ADDR_BATTLE_MON_MAX_HP = 0xD023  # 2 bytes big-endian
ADDR_BATTLE_MON_PP = 0xD02D      # 4 bytes

# Active Battle Memory (Enemy)
ADDR_ENEMY_MON_SPECIES = 0xCFE5
ADDR_ENEMY_MON_HP = 0xCFE6       # 2 bytes big-endian
ADDR_ENEMY_MON_STATUS = 0xCFE9
ADDR_ENEMY_MON_TYPE1 = 0xCFEA
ADDR_ENEMY_MON_TYPE2 = 0xCFEB
ADDR_ENEMY_MON_LEVEL = 0xCFF3
ADDR_ENEMY_MON_MAX_HP = 0xCFF4   # 2 bytes big-endian

# Menu & Text status
ADDR_TEXT_BOX_OPEN = 0xCFC4     # Non-zero if text box is waiting on player A/B input

# Type IDs
TYPES = {
    0x00: "Normal",
    0x01: "Fighting",
    0x02: "Flying",
    0x03: "Poison",
    0x04: "Ground",
    0x05: "Rock",
    0x07: "Bug",
    0x08: "Ghost",
    0x14: "Fire",
    0x15: "Water",
    0x16: "Grass",
    0x17: "Electric",
    0x18: "Psychic",
    0x19: "Ice",
    0x1A: "Dragon",
}

# Common Gen 1 Move IDs to Name
MOVES = {
    1: "Pound",
    10: "Scratch",
    33: "Tackle",
    36: "Take Down",
    43: "Leer",
    45: "Growl",
    52: "Ember",
    53: "Flamethrower",
    55: "Water Gun",
    56: "Hydro Pump",
    57: "Surf",
    72: "Mega Drain",
    73: "Leech Seed",
    75: "Razor Leaf",
    76: "Solar Beam",
    84: "Thunder Shock",
    85: "Thunderbolt",
    87: "Thunder",
    93: "Confusion",
    94: "Psychic",
    98: "Quick Attack",
    99: "Rage",
    126: "Fire Blast",
    157: "Rock Slide",
    163: "Slash",
}

# Map IDs for Key Locations
MAPS = {
    0x00: "Pallet Town",
    0x01: "Viridian City",
    0x02: "Pewter City",
    0x03: "Cerulean City",
    0x04: "Lavender Town",
    0x05: "Vermilion City",
    0x06: "Celadon City",
    0x07: "Fuchsia City",
    0x08: "Cinnabar Island",
    0x09: "Indigo Plateau",
    0x0A: "Saffron City",
    0x0C: "Route 1",
    0x0D: "Route 2",
    0x0E: "Route 3",
    0x0F: "Route 4",
    0x33: "Viridian Forest",
    0x3B: "Mt Moon 1F",
    0x3C: "Mt Moon B1F",
    0x3D: "Mt Moon B2F",
    0x76: "Hall of Fame",
}

# Common Gen 1 Species IDs (Internal Game Boy hex values)
SPECIES = {
    0x03: "Venusaur",
    0x09: "Charizard",
    0x14: "Rattata",
    0x15: "Raticate",
    0x24: "Pikachu",
    0x54: "Pidgey",
    0x55: "Pidgeotto",
    0x59: "Pidgeot",
    0x6B: "Geodude",
    0x6E: "Onix",
    0x99: "Bulbasaur",
    0xB0: "Charmander",
    0xB1: "Squirtle",
    0x85: "Mewtwo",
}
