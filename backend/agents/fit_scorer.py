from __future__ import annotations

import asyncio
import json
import logging
from typing import Any, Dict

import anthropic

from ..config import settings
from ._utils import with_backoff
from .state import ARIAState

logger = logging.getLogger(__name__)

# Weights must sum to 1.0
FIT_DIMENSIONS = {
    "therapeutic_area_match": 0.30,
    "phase_capability":       0.25,
    "geographic_overlap":     0.20,
    "deal_size_fit":          0.15,
    "competitive_timing":     0.10,
}

FIT_SYSTEM = """You are a CRO BD director scoring a pharma/biotech sponsor's strategic fit.

CRO profile (use this as the benchmark):
- Therapeutic expertise: Oncology, Rare Disease, Neuroscience, Immunology
- Phase speciality: Phase II and Phase III (some Phase I/IV)
- Site footprint: United States, Western Europe, APAC (Japan, Australia, South Korea)
- Typical deal size: $5M–$50M per programme

Score the sponsor on each dimension (0–100) and explain your reasoning.

Return ONLY valid JSON — no markdown fences, no explanation:
{
  "dimensions": {
    "therapeutic_area_match": {"score": 0-100, "rationale": "one sentence"},
    "phase_capability":       {"score": 0-100, "rationale": "one sentence"},
    "geographic_overlap":     {"score": 0-100, "rationale": "one sentence"},
    "deal_size_fit":          {"score": 0-100, "rationale": "one sentence"},
    "competitive_timing":     {"score": 0-100, "rationale": "one sentence"}
  },
  "summary": "2–3 sentence overall BD assessment"
}"""


def _strip_fences(text: str) -> str:
    text = text.strip()
    if text.startswith("```"):
        lines = [ln for ln in text.splitlines() if not ln.strip().startswith("```")]
        text = "\n".join(lines).strip()
    return text


async def _parse_or_fix(client, system: str, raw_text: str) -> dict:
    try:
        return json.loads(_strip_fences(raw_text))
    except json.JSONDecodeError as err:
        logger.warning("[FitScorer] JSON parse failed (%s) — asking model to fix", err)
        fix_response = await with_backoff(
            client.messages.create,
            model=settings.aria_model,
            max_tokens=1000,
            system=system,
            messages=[
                {"role": "assistant", "content": raw_text},
                {"role": "user", "content": (
                    f"Your response was not valid JSON. Error: {err}\n"
                    "Return ONLY the corrected JSON object. No explanation, no fences."
                )},
            ],
        )
        fixed = " ".join(
            b.text for b in fix_response.content
            if hasattr(b, "type") and b.type == "text"
        )
        return json.loads(_strip_fences(fixed))


async def fit_scorer_node(state: ARIAState) -> Dict[str, Any]:
    """
    Node 3 — Fit Scorer

    Scores the sponsor against 5 CRO-capability dimensions and computes a
    weighted total (0–100). Rationale per dimension surfaces in the UI.

    Self-skips if "fit" is not listed in execution_plan.agents.
    """
    planned_agents = state.get("execution_plan", {}).get("agents", ["trial", "intel", "fit"])
    if "fit" not in planned_agents:
        logger.info("[FitScorer] Skipped by execution plan")
        return {}

    # Skip if data was pre-seeded from a previous run for the same company
    if state.get("fit_score", {}).get("dimensions"):
        logger.info("[FitScorer] Skipped — fit score preserved from previous run")
        return {}

    company_name = state["company_name"]
    trial_data = state.get("trial_data", {})
    intel_data = state.get("intel_data", {})
    await asyncio.sleep(5)   # brief pause to stay within 30K tokens/min rate limit
    logger.info("[FitScorer] Scoring fit for: %s", company_name)

    # Cap list lengths to keep prompt small
    conditions   = trial_data.get("conditions", [])[:6]
    key_signals  = intel_data.get("key_signals", [])[:3]
    pipeline_upd = intel_data.get("pipeline_updates", [])[:3]
    cro_clues    = intel_data.get("cro_partnership_indicators", [])[:3]

    prompt = f"""Sponsor: {company_name}

Trial Activity:
- Active trials: {trial_data.get('total_count', 0)}
- Phases: {trial_data.get('phases', {})}
- Conditions: {', '.join(conditions)}

Intelligence:
- BD signals: {key_signals}
- Pipeline: {pipeline_upd}
- CRO indicators: {cro_clues}

Score this sponsor's fit across all 5 dimensions."""

    client = anthropic.AsyncAnthropic(api_key=settings.anthropic_api_key)

    try:
        response = await with_backoff(
            client.messages.create,
            model=settings.aria_model,
            max_tokens=1000,
            system=FIT_SYSTEM,
            messages=[{"role": "user", "content": prompt}],
        )

        text = " ".join(
            block.text
            for block in response.content
            if hasattr(block, "type") and block.type == "text"
        )
        parsed = await _parse_or_fix(client, FIT_SYSTEM, text)

        dimensions = parsed.get("dimensions", {})
        total_score = sum(
            dimensions.get(dim, {}).get("score", 0) * weight
            for dim, weight in FIT_DIMENSIONS.items()
        )

        fit_score = {
            "total_score": round(total_score),
            "dimensions": dimensions,
            "summary": parsed.get("summary", ""),
        }

        return {
            "fit_score": fit_score,
            "total_usage": [
                {
                    "agent": "fit_scorer",
                    "input_tokens": response.usage.input_tokens,
                    "output_tokens": response.usage.output_tokens,
                }
            ],
        }

    except Exception as exc:
        logger.error("[FitScorer] Failed: %s", exc)
        return {
            "fit_score": {"total_score": 0, "dimensions": {}, "summary": "Scoring failed."},
            "errors": [f"FitScorer: {exc}"],
            "total_usage": [{"agent": "fit_scorer", "input_tokens": 0, "output_tokens": 0}],
        }
