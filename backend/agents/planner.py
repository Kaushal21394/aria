from __future__ import annotations

import json
import logging
from typing import Any, Dict, List, Literal

import anthropic
from pydantic import BaseModel

from ..config import settings
from ._utils import with_backoff
from .state import ARIAState

logger = logging.getLogger(__name__)


class ExecutionPlan(BaseModel):
    """
    Constrained schema for the planner's routing decision.
    Bounding the plan to a fixed set of agents and output formats keeps
    the pipeline auditable and prevents hallucinated routing.
    """
    agents: List[Literal["trial", "intel", "fit"]]
    output_format: Literal[
        "outreach_email",      # personalised BD cold email
        "competitive_brief",   # landscape + opportunity analysis
        "pipeline_summary",    # pipeline overview with opportunity flags
        "account_snapshot",    # quick exec summary
    ]
    rationale: str  # LLM explains its decision — logged for auditability


PLANNER_SYSTEM = """You are an AI research orchestrator for ARIA, a pharma/biotech intelligence platform.

Given a user's research goal for a specific company, decide:

1. Which data agents to run — choose the MINIMUM set needed:
   - "trial"  → fetch clinical trial data (needed for pipeline, trial activity, or any sponsor research)
   - "intel"  → gather LLM-based market intelligence signals (needed for BD signals, news, competitive context)
   - "fit"    → score sponsor fit against CRO capabilities (needed for fit assessment, partnership potential, or outreach)

2. What output format to produce — pick exactly one:
   - "outreach_email"    → personalised BD cold email to sponsor's clinical/R&D leadership
   - "competitive_brief" → structured competitive landscape and BD opportunity analysis
   - "pipeline_summary"  → focused pipeline overview with opportunity flags
   - "account_snapshot"  → quick executive summary (who, what, why it matters)

Return ONLY valid JSON — no markdown fences, no explanation:
{
  "agents": ["trial", "intel", "fit"],
  "output_format": "outreach_email",
  "rationale": "one sentence explaining the routing decision"
}"""


def _strip_fences(text: str) -> str:
    text = text.strip()
    if text.startswith("```"):
        lines = [ln for ln in text.splitlines() if not ln.strip().startswith("```")]
        text = "\n".join(lines).strip()
    return text


_DEFAULT_PLAN: Dict[str, Any] = {
    "agents": ["trial", "intel", "fit"],
    "output_format": "outreach_email",
    "rationale": "No goal specified — running full pipeline with outreach email output.",
}


async def planner_node(state: ARIAState) -> Dict[str, Any]:
    """
    Node 0 — Planner

    Reads the user's natural language goal and produces an ExecutionPlan:
    - agents: which nodes to run (minimum set for the goal)
    - output_format: what the synthesizer should produce
    - rationale: why — logged and stored for debugging/auditability

    Falls back to the full pipeline + outreach_email if the goal is empty
    or if the LLM call fails.
    """
    company_name = state["company_name"]
    user_goal = state.get("user_goal", "").strip()

    if not user_goal:
        logger.info("[Planner] No goal provided — using default plan")
        return {"execution_plan": _DEFAULT_PLAN}

    logger.info("[Planner] Planning for: '%s' (company: %s)", user_goal, company_name)

    prompt = f"Company: {company_name}\nGoal: {user_goal}\n\nProduce the execution plan."
    client = anthropic.AsyncAnthropic(api_key=settings.anthropic_api_key)

    try:
        response = await with_backoff(
            client.messages.create,
            model=settings.aria_model,
            max_tokens=256,
            system=PLANNER_SYSTEM,
            messages=[{"role": "user", "content": prompt}],
        )

        text = " ".join(
            b.text for b in response.content
            if hasattr(b, "type") and b.type == "text"
        )
        parsed = json.loads(_strip_fences(text))
        plan = ExecutionPlan(**parsed)  # validates agents + output_format are in allowed set

        logger.info(
            "[Planner] Plan: agents=%s format=%s | %s",
            plan.agents, plan.output_format, plan.rationale,
        )

        return {
            "execution_plan": plan.model_dump(),
            "total_usage": [{
                "agent": "planner",
                "input_tokens": response.usage.input_tokens,
                "output_tokens": response.usage.output_tokens,
            }],
        }

    except Exception as exc:
        logger.error("[Planner] Failed (%s) — falling back to default plan", exc)
        return {
            "execution_plan": {
                **_DEFAULT_PLAN,
                "rationale": f"Planner failed ({exc}), using full pipeline fallback.",
            },
            "errors": [f"Planner: {exc}"],
            "total_usage": [{"agent": "planner", "input_tokens": 0, "output_tokens": 0}],
        }
