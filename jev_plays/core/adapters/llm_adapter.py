"""
Surrogate LLM Adapter for Jev System One.
Connects to local LiteLLM, Ollama, or OpenAI-compatible endpoints to provide
real AI inference with typed System-1 schemas while on the Jev waitlist.
"""

from __future__ import annotations

import json
import logging
import os
import re
from typing import Any, Dict, Optional

import httpx
from typesafe_sdk import (
    Choice,
    ChoiceAnswer,
    Noul,
    NoulAnswer,
    Score,
    ScoreAnswer,
    SystemOneResponse,
    Usage,
)

logger = logging.getLogger(__name__)


class SystemOneLLMAdapter:
    def __init__(
        self,
        api_base: Optional[str] = None,
        api_key: Optional[str] = None,
        model: Optional[str] = None,
        timeout: float = 6.0,
    ):
        self.api_base = (
            api_base
            or os.environ.get("LITELLM_API_BASE")
            or "http://localhost:4000"
        ).rstrip("/")
        # Ensure /v1 endpoint
        if not self.api_base.endswith("/v1"):
            self.endpoint = f"{self.api_base}/v1/chat/completions"
        else:
            self.endpoint = f"{self.api_base}/chat/completions"

        self.api_key = (
            api_key
            or os.environ.get("LITELLM_API_KEY")
            or "sk-067cb3a95cba9512660ebbb13393db6912413f4d9df9e146"
        )
        self.model = model or os.environ.get("SURROGATE_MODEL", "deepseek-flash-nothink")
        self.timeout = timeout
        self.http_client = httpx.Client(timeout=self.timeout)

    def _build_prompt(self, state: Dict[str, Any], questions: Dict[str, Any]) -> str:
        prompt_lines = [
            "You are acting as an ultra-fast System 1 decision engine for a game agent.",
            "Analyze the given Game State and immediately answer each question.",
            "Respond ONLY with valid JSON matching the specified schema. Do not write markdown, greetings, or commentary.",
            "",
            "--- GAME STATE ---",
            json.dumps(state, indent=2),
            "",
            "--- QUESTIONS TO ANSWER ---",
        ]

        expected_schema = {}
        for q_name, q_spec in questions.items():
            if isinstance(q_spec, Choice):
                prompt_lines.append(f"Question '{q_name}' (Choice): {q_spec.instructions}")
                prompt_lines.append(f"  Valid Options: {json.dumps(q_spec.criteria)}")
                first_opt = list(q_spec.criteria.keys())[0] if q_spec.criteria else "default"
                expected_schema[q_name] = {"choice": first_opt, "confidence": 0.95}
            elif isinstance(q_spec, Noul):
                prompt_lines.append(f"Question '{q_name}' (Noul): {q_spec.instructions}")
                prompt_lines.append("  Output: A calibrated probability from 0.0 (false) to 1.0 (true).")
                expected_schema[q_name] = {"noul": 0.1}
            elif isinstance(q_spec, Score):
                prompt_lines.append(f"Question '{q_name}' (Score): {q_spec.instructions}")
                prompt_lines.append(f"  Rubric (ordered index 0 to N): {json.dumps(q_spec.criteria)}")
                expected_schema[q_name] = {"score": 0.0, "confidence": 0.9}

        prompt_lines.extend([
            "",
            "--- REQUIRED JSON OUTPUT FORMAT ---",
            json.dumps(expected_schema, indent=2),
        ])

        return "\n".join(prompt_lines)

    def _parse_llm_response(
        self, raw_text: str, questions: Dict[str, Any]
    ) -> SystemOneResponse:
        # Extract JSON from potential codeblocks
        text = raw_text.strip()
        json_match = re.search(r"(\{.*\})", text, re.DOTALL)
        if json_match:
            text = json_match.group(1)

        try:
            data = json.loads(text)
        except Exception:
            logger.warning(f"Failed to parse JSON from surrogate model: {text[:200]}")
            data = {}

        answers: Dict[str, Any] = {}
        for q_name, q_spec in questions.items():
            q_res = data.get(q_name, {}) if isinstance(data, dict) else {}

            if isinstance(q_spec, Choice):
                keys = list(q_spec.criteria.keys()) if q_spec.criteria else ["default"]
                chosen = q_res.get("choice") if isinstance(q_res, dict) else str(q_res)
                if chosen not in keys:
                    chosen = keys[0]
                conf = float(q_res.get("confidence", 0.9)) if isinstance(q_res, dict) else 0.9
                answers[q_name] = ChoiceAnswer(
                    type="choice",
                    choice=str(chosen),
                    confidence=conf,
                    probabilities={k: 1.0 if k == chosen else 0.0 for k in keys},
                )

            elif isinstance(q_spec, Noul):
                val = q_res.get("noul", 0.1) if isinstance(q_res, dict) else 0.1
                try:
                    val_float = float(val)
                except Exception:
                    val_float = 0.9 if bool(val) else 0.1
                answers[q_name] = NoulAnswer(type="noul", noul=val_float)

            elif isinstance(q_spec, Score):
                criteria = q_spec.criteria or ["Low", "Medium", "High"]
                val = q_res.get("score", 0.0) if isinstance(q_res, dict) else 0.0
                try:
                    val_float = float(val)
                except Exception:
                    val_float = 0.0
                conf = float(q_res.get("confidence", 0.85)) if isinstance(q_res, dict) else 0.85
                legend = {i: str(c) for i, c in enumerate(criteria)}
                prob = {i: round(1.0 / len(criteria), 2) for i in range(len(criteria))}
                answers[q_name] = ScoreAnswer(
                    type="score",
                    score=val_float,
                    confidence=conf,
                    legend=legend,
                    probabilities=prob,
                )

        return SystemOneResponse(
            model=f"surrogate-{self.model}",
            usage=Usage(input_tokens=150, output_tokens=len(questions) * 10),
            answers=answers,
        )

    def decide(
        self, state: Dict[str, Any], questions: Dict[str, Any]
    ) -> SystemOneResponse:
        prompt = self._build_prompt(state, questions)
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
        }
        payload = {
            "model": self.model,
            "messages": [
                {
                    "role": "system",
                    "content": "You are a low-latency System 1 AI decision engine. You output strict JSON only.",
                },
                {"role": "user", "content": prompt},
            ],
            "temperature": 0.1,
            "response_format": {"type": "json_object"},
        }

        try:
            resp = self.http_client.post(self.endpoint, headers=headers, json=payload)
            resp.raise_for_status()
            res_data = resp.json()
            content = res_data["choices"][0]["message"]["content"]
            return self._parse_llm_response(content, questions)
        except Exception as e:
            logger.error(f"Error calling surrogate endpoint ({self.endpoint}): {e}")
            # Fallback gracefully
            return self._parse_llm_response("{}", questions)
