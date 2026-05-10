from __future__ import annotations

import json
import logging
from typing import Any, Dict

import anthropic

from ..config import settings
from ._utils import with_backoff
from .state import ARIAState

logger = logging.getLogger(__name__)

# Web search is disabled at this tier (30K tokens/min) — each search call
# injects full page content into context, easily consuming the entire budget
# in one shot. Re-enable in Phase 4 when on a higher rate-limit tier.
_WEB_SEARCH_ENABLED = False

INTEL_SYSTEM = """You are a pharma/biotech intelligence analyst embedded in a CRO BD team.
Using your training knowledge, extract actionable BD intelligence signals for the given sponsor.

Return ONLY valid JSON — no markdown fences, no explanation.
Keep every string value under 120 characters so the response fits within token limits.
{
  "key_signals": ["up to 4 BD opportunity signals"],
  "recent_news": ["up to 3 pipeline milestones or approvals"],
  "pipeline_updates": ["up to 3 phase transitions or partnerships"],
  "cro_partnership_indicators": ["up to 3 outsourcing or CRO signals"]
}"""


def _strip_fences(text: str) -> str:
    text = text.strip()
    if text.startswith("```"):
        lines = [ln for ln in text.splitlines() if not ln.strip().startswith("```")]
        text = "\n".join(lines).strip()
    return text


def _try_salvage(raw_text: str) -> dict | None:
    """
    If the JSON is truncated mid-string, attempt to close it so it parses.
    Works for the common case where the response was cut off inside a list/object.
    Returns a parsed dict or None if salvage fails.
    """
    text = _strip_fences(raw_text).rstrip()
    # Walk closing brackets/braces until we get a valid parse
    for suffix in ["]}}", '"]}}', '"]}', '"]', "}}", "}"]:
        try:
            return json.loads(text + suffix)
        except json.JSONDecodeError:
            continue
    return None


async def _parse_or_fix(client, raw_text: str) -> dict:
    """
    Try to parse raw_text as JSON.
    1. Direct parse
    2. Structural salvage (close truncated brackets)
    3. One-shot model correction
    """
    # 1. Direct parse
    try:
        return json.loads(_strip_fences(raw_text))
    except json.JSONDecodeError as err:
        logger.warning("[IntelAgent] JSON parse failed (%s) — attempting salvage", err)

    # 2. Salvage truncated output
    salvaged = _try_salvage(raw_text)
    if salvaged is not None:
        logger.info("[IntelAgent] Salvaged truncated JSON successfully")
        return salvaged

    # 3. Ask the model to rewrite it from scratch (not from the broken output)
    logger.warning("[IntelAgent] Salvage failed — asking model to rewrite")
    fix_response = await with_backoff(
        client.messages.create,
        model=settings.aria_model,
        max_tokens=800,
        system=INTEL_SYSTEM,
        messages=[
            {"role": "user", "content": (
                "The previous response was truncated and could not be parsed as JSON. "
                "Rewrite it now as a complete, valid JSON object. "
                "Keep all string values under 80 characters. "
                "No markdown fences, no explanation."
            )},
        ],
    )
    fixed_text = " ".join(
        b.text for b in fix_response.content
        if hasattr(b, "type") and b.type == "text"
    )
    return json.loads(_strip_fences(fixed_text))


async def intel_agent_node(state: ARIAState) -> Dict[str, Any]:
    """
    Node 2 — Intel Agent

    Uses Claude's training knowledge to produce BD intelligence signals.
    Web search is disabled at the free-tier rate limit (30K tokens/min) —
    search results inflate context to 15–30K tokens per call, which exhausts
    the per-minute budget before other agents can run.

    Self-skips if "intel" is not listed in execution_plan.agents.
    """
    planned_agents = state.get("execution_plan", {}).get("agents", ["trial", "intel", "fit"])
    if "intel" not in planned_agents:
        logger.info("[IntelAgent] Skipped by execution plan")
        return {}

    # Skip if data was pre-seeded from a previous run for the same company
    if state.get("intel_data", {}).get("key_signals"):
        logger.info("[IntelAgent] Skipped — intel data preserved from previous run")
        return {}

    company_name = state["company_name"]
    trial_data = state.get("trial_data", {})
    logger.info("[IntelAgent] Gathering intelligence for: %s", company_name)

    # Keep the prompt short — only the most relevant trial signals
    phases     = trial_data.get("phases", {})
    conditions = ", ".join(trial_data.get("conditions", [])[:5])
    total      = trial_data.get("total_count", 0)

    prompt = (
        f"Sponsor: {company_name}\n"
        f"Active trials: {total} | Phases: {phases} | Key conditions: {conditions}\n\n"
        f"Provide BD intelligence signals for this sponsor."
    )

    client = anthropic.AsyncAnthropic(api_key=settings.anthropic_api_key)

    try:
        response = await with_backoff(
            client.messages.create,
            model=settings.aria_model,
            max_tokens=1024,
            system=INTEL_SYSTEM,
            messages=[{"role": "user", "content": prompt}],
        )

        text = " ".join(
            block.text
            for block in response.content
            if hasattr(block, "type") and block.type == "text"
        )
        intel_data = await _parse_or_fix(client, text)

        return {
            "intel_data": intel_data,
            "total_usage": [
                {
                    "agent": "intel_agent",
                    "input_tokens": response.usage.input_tokens,
                    "output_tokens": response.usage.output_tokens,
                }
            ],
        }

    except Exception as exc:
        logger.error("[IntelAgent] Failed: %s", exc)
        return {
            "intel_data": {
                "key_signals": [],
                "recent_news": [],
                "pipeline_updates": [],
                "cro_partnership_indicators": [],
            },
            "errors": [f"IntelAgent: {exc}"],
            "total_usage": [{"agent": "intel_agent", "input_tokens": 0, "output_tokens": 0}],
        }
