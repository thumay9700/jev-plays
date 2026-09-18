"""
Tactical combat decision engine for Pokémon Red using TypeSafe AI's Jev primitives.
"""

from __future__ import annotations

from typing import Any, Dict, Tuple
from typesafe_sdk import Choice, Noul, Score

from .state import PokemonRedState


class CombatTactician:
    """Builds typed Jev System One questions for combat encounters."""

    @staticmethod
    def get_move_criteria(moves: list[str], enemy_types: list[str]) -> Dict[str, str]:
        criteria = {}
        for m in moves:
            # Descriptive criteria to guide Jev's System 1 selection
            m_lower = m.lower()
            if any(t in m_lower for t in ["ember", "flame", "blast"]):
                effect = "Fire type (effective vs Grass/Bug/Ice; weak vs Water/Rock/Dragon)"
            elif any(t in m_lower for t in ["water", "surf", "hydro"]):
                effect = "Water type (effective vs Fire/Ground/Rock; weak vs Grass/Electric/Dragon)"
            elif any(t in m_lower for t in ["thunder", "shock"]):
                effect = "Electric type (effective vs Water/Flying; ineffective vs Ground)"
            elif any(t in m_lower for t in ["vine", "leaf", "drain", "seed"]):
                effect = "Grass type (effective vs Water/Ground/Rock; weak vs Fire/Flying/Bug)"
            elif any(t in m_lower for t in ["psychic", "confusion"]):
                effect = "Psychic type (very strong in Gen 1; effective vs Fighting/Poison)"
            elif any(t in m_lower for t in ["slash", "cut"]):
                effect = "High critical-hit physical attack"
            else:
                effect = "Standard physical damage attack"

            criteria[m] = f"{effect}. Opponent types: {', '.join(enemy_types)}"

        return criteria

    def build_combat_questions(self, state: PokemonRedState) -> Dict[str, Any]:
        player = state.battle.player_mon
        enemy = state.battle.enemy_mon
        is_wild = state.battle.battle_type == "wild"

        # Action choices
        action_criteria = {
            "fight": "Execute one of our attacks against the opponent.",
            "item": "Use an item (such as a potion) from the bag.",
        }
        if is_wild:
            action_criteria["run"] = "Attempt to flee from this wild encounter."
        action_criteria["switch"] = "Switch to another healthy Pokémon in the party."

        questions: Dict[str, Any] = {
            "battle_action": Choice(
                instructions="Determine the primary action for this combat turn.",
                criteria=action_criteria,
            ),
            "should_heal": Noul(
                instructions="Should we use a healing item (Potion) right now based on our current HP percentage?"
            ),
            "wipe_risk": Score(
                instructions="Rate the immediate risk of our active Pokémon fainting in the next 1-2 turns.",
                criteria=["Minimal", "Guarded", "Elevated", "Severe", "Critical"],
            ),
        }

        if player and player.moves:
            move_criteria = self.get_move_criteria(player.moves, enemy.types if enemy else ["Normal"])
            questions["selected_move"] = Choice(
                instructions="Select the optimal attack move to use against the opponent.",
                criteria=move_criteria,
            )

        return questions

    def interpret_decision(self, response_answers: Dict[str, Any]) -> Tuple[str, Dict[str, Any]]:
        """
        Parses Jev's answers into a concrete combat directive.
        Returns (directive_name, telemetry_details).
        """
        action_ans = response_answers.get("battle_action")
        heal_ans = response_answers.get("should_heal")
        move_ans = response_answers.get("selected_move")
        risk_ans = response_answers.get("wipe_risk")

        action = getattr(action_ans, "choice", "fight")
        heal_val = getattr(heal_ans, "noul", 0.0)
        should_heal = bool(heal_val >= 0.5) if isinstance(heal_val, (int, float)) else bool(heal_val)
        chosen_move = getattr(move_ans, "choice", "Tackle")
        risk_score = getattr(risk_ans, "score", 0.0)

        # If Jev explicitly says to heal, prioritize item
        if should_heal and action != "item":
            action = "item"

        return action, {
            "action": action,
            "move": chosen_move,
            "should_heal": should_heal,
            "risk_level": risk_score,
        }
