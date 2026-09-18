from jev_plays.games.pokemon_red.navigator import OverworldNavigator
from jev_plays.games.pokemon_red.state import PokemonRedState, BattleState, OverworldState


def test_navigator_waypoints():
    nav = OverworldNavigator()

    # In Pallet Town (Map 0x00)
    battle = BattleState(in_battle=False, battle_type="none")
    overworld = OverworldState(map_id=0x00, map_name="Pallet Town", x=5, y=5, badges=0, is_hall_of_fame=False)
    state = PokemonRedState(is_in_battle=False, battle=battle, overworld=overworld, text_active=False)

    step = nav.get_navigation_step(state)
    assert step == "UP"

    # Inside Oak's Lab (Map 0x28) near waypoint (5, 3)
    overworld_lab = OverworldState(map_id=0x28, map_name="Oak's Lab", x=5, y=3, badges=0, is_hall_of_fame=False)
    state_lab = PokemonRedState(is_in_battle=False, battle=battle, overworld=overworld_lab, text_active=False)

    step_lab = nav.get_navigation_step(state_lab)
    # Arrived at waypoint, should advance to next waypoint and press A
    assert step_lab == "A"
    assert nav.current_waypoint_index == 1
    assert nav.current_waypoint.name == "Route 1 North"
