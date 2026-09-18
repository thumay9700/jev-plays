"""
Jev decision client wrapper.
Communicates with TypeSafe AI System One models, tracks latency and token usage,
and provides an intelligent mock mode for offline testing and development.
"""

from __future__ import annotations

import logging
import os
import random
import time
from typing import Any, Dict, Optional

from typesafe_sdk import (
    Choice,
    ChoiceAnswer,
    Noul,
    NoulAnswer,
    Score,
    ScoreAnswer,
    SystemOneResponse,
    TypeSafeClient,
    Usage,
)

from .telemetry import TelemetryTracker

logger = logging.getLogger(__name__)


class MockSystemOneEngine:
    """Intelligent mock decision engine when no API key is configured."""

    def decide(
        self, state: Dict[str, Any], questions: Dict[str, Any]
    ) -> SystemOneResponse:
        answers: Dict[str, Any] = {}

        for q_name, q_spec in questions.items():
            if isinstance(q_spec, Choice):
                keys = list(q_spec.criteria.keys()) if q_spec.criteria else ["default"]
                # If question is in battle, pick the smartest option based on simple state
                chosen = keys[0]
                if "selected_move" in q_name or "move" in q_name:
                    # Prefer high damage moves or super-effective keywords if available
                    for k in keys:
                        crit = str(q_spec.criteria.get(k, "")).lower()
                        if "high damage" in crit or "effective" in crit:
                            chosen = k
                            break
                    else:
                        chosen = keys[0]
                elif "battle_action" in q_name:
                    # If HP low and items present, item; else fight
                    player_hp = state.get("player_pokemon", {}).get("hp_percent", 1.0)
                    if player_hp < 0.25 and "item" in keys and state.get("has_healing_items"):
                        chosen = "item"
                    elif "fight" in keys:
                        chosen = "fight"
                    else:
                        chosen = keys[0]
                else:
                    chosen = random.choice(keys)

                answers[q_name] = ChoiceAnswer(
                    type="choice",
                    choice=chosen,
                    confidence=round(random.uniform(0.85, 0.99), 3),
                    probabilities={k: 1.0 if k == chosen else 0.0 for k in keys},
                )

            elif isinstance(q_spec, Noul):
                # Simple boolean heuristic
                if "heal" in q_name or "should_heal" in q_name:
                    hp = state.get("player_pokemon", {}).get("hp_percent", 1.0)
                    val = hp < 0.35 and state.get("has_healing_items", False)
                else:
                    val = bool(random.getrandbits(1))
                noul_score = 0.95 if val else 0.05
                answers[q_name] = NoulAnswer(type="noul", noul=noul_score)

            elif isinstance(q_spec, Score):
                criteria = q_spec.criteria or ["Low", "Medium", "High"]
                idx = len(criteria) // 2
                legend = {i: str(c) for i, c in enumerate(criteria)}
                prob = {i: round(1.0 / len(criteria), 2) for i in range(len(criteria))}
                answers[q_name] = ScoreAnswer(
                    type="score",
                    score=float(idx),
                    confidence=round(random.uniform(0.80, 0.95), 2),
                    legend=legend,
                    probabilities=prob,
                )


        return SystemOneResponse(
            model="jev-system-1-mock",
            usage=Usage(input_tokens=120, output_tokens=len(questions)),
            answers=answers,
        )


class JevDecisionClient:
    def __init__(
        self,
        api_key: Optional[str] = None,
        model: Optional[str] = None,
        telemetry: Optional[TelemetryTracker] = None,
        mock_mode: bool = False,
        backend: Optional[str] = None,
        llm_api_base: Optional[str] = None,
        llm_api_key: Optional[str] = None,
        llm_model: Optional[str] = None,
    ):
        self.api_key = api_key or os.environ.get("TYPESAFE_API_KEY")
        self.telemetry = telemetry or TelemetryTracker()
        self.mock_engine = MockSystemOneEngine()

        # Determine backend
        if mock_mode:
            self.backend = "mock"
        elif backend:
            self.backend = backend.lower()
        elif self.api_key:
            self.backend = "jev"
        else:
            self.backend = "litellm"

        self.client = None
        self.llm_adapter = None

        if self.backend == "jev":
            logger.info("Initializing live TypeSafeClient with Jev System One model.")
            self.client = TypeSafeClient(api_key=self.api_key, model=model)
        elif self.backend == "litellm":
            from .adapters.llm_adapter import SystemOneLLMAdapter
            logger.info("Initializing SystemOneLLMAdapter (local LiteLLM / surrogate model mode).")
            self.llm_adapter = SystemOneLLMAdapter(
                api_base=llm_api_base,
                api_key=llm_api_key,
                model=llm_model,
            )
        else:
            logger.info("JevDecisionClient running in MOCK mode.")
            self.backend = "mock"

    def decide(
        self, state: Dict[str, Any], questions: Dict[str, Any]
    ) -> SystemOneResponse:
        start_time = time.perf_counter()

        if self.backend == "jev" and self.client:
            resp = self.client.system_one(state=state, questions=questions)
        elif self.backend == "litellm" and self.llm_adapter:
            resp = self.llm_adapter.decide(state=state, questions=questions)
        else:
            # Simulate real network latency (50-100ms)
            time.sleep(random.uniform(0.04, 0.08))
            resp = self.mock_engine.decide(state=state, questions=questions)

        elapsed_ms = (time.perf_counter() - start_time) * 1000.0

        self.telemetry.record_decision(
            latency_ms=elapsed_ms,
            model=getattr(resp, "model", "jev-system-1"),
            answers=resp.answers,
            usage=getattr(resp, "usage", None),
        )

        return resp
