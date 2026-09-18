import json
from pathlib import Path
from typesafe_sdk import Choice, Noul, Score
from jev_plays.core.jev_client import JevDecisionClient
from jev_plays.core.telemetry import TelemetryTracker


def test_mock_jev_client_decisions(tmp_path):
    overlay_file = tmp_path / "hud.json"
    telemetry = TelemetryTracker(overlay_file=overlay_file)
    client = JevDecisionClient(telemetry=telemetry, mock_mode=True)

    state = {
        "player_pokemon": {"species": "Charizard", "hp_percent": 0.20},
        "opponent_pokemon": {"species": "Blastoise", "hp_percent": 0.80},
        "has_healing_items": True,
    }

    questions = {
        "battle_action": Choice(
            instructions="Pick action",
            criteria={"fight": "Attack", "item": "Use potion"},
        ),
        "should_heal": Noul(instructions="Should heal?"),
        "danger": Score(instructions="Risk level", criteria=["Low", "Medium", "High"]),
    }

    response = client.decide(state=state, questions=questions)

    assert response is not None
    assert "battle_action" in response.answers
    assert "should_heal" in response.answers
    assert "danger" in response.answers

    # Verify answers
    action_ans = response.answers["battle_action"]
    heal_ans = response.answers["should_heal"]
    danger_ans = response.answers["danger"]

    assert isinstance(heal_ans.noul, float)
    assert 0.0 <= heal_ans.noul <= 1.0
    assert danger_ans.score in [0, 1, 2]

    # Verify telemetry
    assert telemetry.total_calls == 1
    assert telemetry.avg_latency_ms > 0
    assert overlay_file.exists()

    with open(overlay_file, "r") as f:
        hud_data = json.load(f)
        assert hud_data["total_calls"] == 1
        assert "battle_action" in hud_data["latest_decisions"]
