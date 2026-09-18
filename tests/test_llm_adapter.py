import json
from typesafe_sdk import Choice, Noul, Score
from jev_plays.core.adapters.llm_adapter import SystemOneLLMAdapter


def test_llm_adapter_prompt_building():
    adapter = SystemOneLLMAdapter(
        api_base="http://localhost:4000/v1",
        api_key="sk-test",
        model="deepseek-flash-nothink",
    )

    state = {"player_pokemon": {"species": "Pikachu", "hp_percent": 0.5}}
    questions = {
        "battle_action": Choice(instructions="Action", criteria={"fight": "Attack", "item": "Heal"}),
        "should_heal": Noul(instructions="Should heal?"),
        "danger": Score(instructions="Danger rating", criteria=["Safe", "Danger"]),
    }

    prompt = adapter._build_prompt(state, questions)
    assert "Pikachu" in prompt
    assert "battle_action" in prompt
    assert "should_heal" in prompt
    assert "danger" in prompt


def test_llm_adapter_response_parsing():
    adapter = SystemOneLLMAdapter(
        api_base="http://localhost:4000/v1",
        api_key="sk-test",
        model="deepseek-flash-nothink",
    )

    questions = {
        "battle_action": Choice(instructions="Action", criteria={"fight": "Attack", "item": "Heal"}),
        "should_heal": Noul(instructions="Should heal?"),
        "danger": Score(instructions="Danger rating", criteria=["Safe", "Danger"]),
    }

    llm_json_output = json.dumps({
        "battle_action": {"choice": "fight", "confidence": 0.95},
        "should_heal": {"noul": 0.1},
        "danger": {"score": 0.0, "confidence": 0.9},
    })

    resp = adapter._parse_llm_response(llm_json_output, questions)

    assert resp is not None
    assert "battle_action" in resp.answers
    assert resp.answers["battle_action"].choice == "fight"
    assert resp.answers["should_heal"].noul == 0.1
    assert resp.answers["danger"].score == 0.0
