from typesafe_sdk import ChoiceAnswer, NoulAnswer, ScoreAnswer
from jev_plays.games.pokemon_red.tactics import CombatTactician
from jev_plays.games.pokemon_red.state import PokemonRedState, BattleState, OverworldState, ActivePokemon


def test_combat_tactician_questions():
    tactician = CombatTactician()

    player_mon = ActivePokemon(
        species="Squirtle",
        level=10,
        current_hp=28,
        max_hp=28,
        hp_percent=1.0,
        types=["Water"],
        moves=["Tackle", "Water Gun", "Bubble"],
        status="normal",
    )
    enemy_mon = ActivePokemon(
        species="Geodude",
        level=12,
        current_hp=30,
        max_hp=30,
        hp_percent=1.0,
        types=["Rock", "Ground"],
        moves=["Tackle"],
        status="normal",
    )
    battle = BattleState(in_battle=True, battle_type="trainer", player_mon=player_mon, enemy_mon=enemy_mon)
    overworld = OverworldState(map_id=0x36, map_name="Pewter Gym", x=4, y=3, badges=0, is_hall_of_fame=False)
    state = PokemonRedState(is_in_battle=True, battle=battle, overworld=overworld, text_active=False)

    questions = tactician.build_combat_questions(state)

    assert "battle_action" in questions
    assert "should_heal" in questions
    assert "selected_move" in questions
    assert "wipe_risk" in questions

    # Check criteria includes Water Gun
    move_q = questions["selected_move"]
    assert "Water Gun" in move_q.criteria
    assert "Water type" in move_q.criteria["Water Gun"]


def test_tactician_interpret_decision():
    tactician = CombatTactician()

    answers = {
        "battle_action": ChoiceAnswer(
            type="choice",
            choice="fight",
            confidence=0.98,
            probabilities={"fight": 0.98, "item": 0.02},
        ),
        "should_heal": NoulAnswer(type="noul", noul=0.1),
        "selected_move": ChoiceAnswer(
            type="choice",
            choice="Water Gun",
            confidence=0.95,
            probabilities={"Water Gun": 0.95, "Tackle": 0.05},
        ),
        "wipe_risk": ScoreAnswer(
            type="score",
            score=0.0,
            confidence=0.9,
            legend={0: "Minimal", 1: "Guarded", 2: "Elevated", 3: "Severe", 4: "Critical"},
            probabilities={0: 0.9, 1: 0.05, 2: 0.05, 3: 0.0, 4: 0.0},
        ),
    }

    action, details = tactician.interpret_decision(answers)
    assert action == "fight"
    assert details["move"] == "Water Gun"
    assert details["should_heal"] is False

    # Test heal override
    answers_heal = {
        "battle_action": ChoiceAnswer(
            type="choice",
            choice="fight",
            confidence=0.8,
            probabilities={"fight": 0.8, "item": 0.2},
        ),
        "should_heal": NoulAnswer(type="noul", noul=0.9),
        "selected_move": ChoiceAnswer(
            type="choice",
            choice="Tackle",
            confidence=0.5,
            probabilities={"Tackle": 1.0},
        ),
        "wipe_risk": ScoreAnswer(
            type="score",
            score=4.0,
            confidence=0.9,
            legend={0: "Minimal", 1: "Guarded", 2: "Elevated", 3: "Severe", 4: "Critical"},
            probabilities={0: 0.0, 1: 0.0, 2: 0.0, 3: 0.1, 4: 0.9},
        ),
    }
    action_heal, details_heal = tactician.interpret_decision(answers_heal)
    assert action_heal == "item"
    assert details_heal["should_heal"] is True

