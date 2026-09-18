"""
Telemetry and metrics tracker for Jev decisions.
Provides real-time stats (latency, confidence, call counts, costs)
and exports live JSON state for video stream overlays / HUDs.
"""

from __future__ import annotations

import json
import time
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, List, Optional


@dataclass
class DecisionRecord:
    timestamp: float
    latency_ms: float
    question_count: int
    confidence_avg: float
    model: str
    summary: Dict[str, Any]


class TelemetryTracker:
    def __init__(self, overlay_file: Optional[str | Path] = None):
        self.overlay_file = Path(overlay_file) if overlay_file else None
        self.total_calls: int = 0
        self.total_tokens_in: int = 0
        self.total_tokens_out: int = 0
        self.latencies: List[float] = []
        self.records: List[DecisionRecord] = []
        self.cost_estimate_usd: float = 0.0

        # Cost parameters for TypeSafe Jev ($0.0003 per call baseline)
        self.cost_per_call = 0.0003

    def record_decision(
        self,
        latency_ms: float,
        model: str,
        answers: Dict[str, Any],
        usage: Optional[Any] = None,
    ) -> DecisionRecord:
        self.total_calls += 1
        self.latencies.append(latency_ms)
        self.cost_estimate_usd += self.cost_per_call

        confidences = []
        summary = {}
        for q_name, ans in answers.items():
            ans_type = getattr(ans, "type", "unknown")
            if ans_type == "choice":
                conf = getattr(ans, "confidence", 1.0)
                confidences.append(conf)
                summary[q_name] = {
                    "type": "choice",
                    "value": getattr(ans, "choice", ""),
                    "confidence": conf,
                }
            elif ans_type == "noul":
                summary[q_name] = {
                    "type": "noul",
                    "value": getattr(ans, "noul", False),
                }
            elif ans_type == "score":
                conf = getattr(ans, "confidence", 1.0)
                confidences.append(conf)
                summary[q_name] = {
                    "type": "score",
                    "value": getattr(ans, "score", 0),
                    "confidence": conf,
                }
            else:
                summary[q_name] = {"value": str(ans)}

        avg_conf = sum(confidences) / len(confidences) if confidences else 1.0

        if usage:
            self.total_tokens_in += getattr(usage, "input_tokens", 0) or 0
            self.total_tokens_out += getattr(usage, "output_tokens", 0) or 0

        rec = DecisionRecord(
            timestamp=time.time(),
            latency_ms=latency_ms,
            question_count=len(answers),
            confidence_avg=avg_conf,
            model=model,
            summary=summary,
        )
        self.records.append(rec)

        if self.overlay_file:
            self.export_hud_state()

        return rec

    @property
    def avg_latency_ms(self) -> float:
        return sum(self.latencies) / len(self.latencies) if self.latencies else 0.0

    @property
    def p95_latency_ms(self) -> float:
        if not self.latencies:
            return 0.0
        sorted_l = sorted(self.latencies)
        idx = int(len(sorted_l) * 0.95)
        return sorted_l[min(idx, len(sorted_l) - 1)]

    def get_stats_summary(self) -> Dict[str, Any]:
        return {
            "total_calls": self.total_calls,
            "avg_latency_ms": round(self.avg_latency_ms, 2),
            "p95_latency_ms": round(self.p95_latency_ms, 2),
            "min_latency_ms": round(min(self.latencies), 2) if self.latencies else 0.0,
            "max_latency_ms": round(max(self.latencies), 2) if self.latencies else 0.0,
            "tokens_in": self.total_tokens_in,
            "tokens_out": self.total_tokens_out,
            "estimated_cost_usd": round(self.cost_estimate_usd, 4),
        }

    def export_hud_state(self) -> None:
        """Writes real-time HUD data for video overlay / OBS / graphics."""
        if not self.overlay_file:
            return

        last_rec = self.records[-1] if self.records else None
        hud_payload = {
            "model": "TypeSafe Jev (System 1)",
            "total_calls": self.total_calls,
            "latest_latency_ms": round(last_rec.latency_ms, 1) if last_rec else 0,
            "avg_latency_ms": round(self.avg_latency_ms, 1),
            "latest_confidence": round(last_rec.confidence_avg * 100, 1) if last_rec else 100.0,
            "cost_usd": f"${self.cost_estimate_usd:.3f}",
            "latest_decisions": last_rec.summary if last_rec else {},
            "timestamp": time.time(),
        }

        self.overlay_file.parent.mkdir(parents=True, exist_ok=True)
        with open(self.overlay_file, "w", encoding="utf-8") as f:
            json.dump(hud_payload, f, indent=2)
