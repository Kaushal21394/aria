from __future__ import annotations

import logging
from typing import Any, Dict, List

from ..services.clinical_trials import fetch_trials
from .state import ARIAState

logger = logging.getLogger(__name__)


async def trial_agent_node(state: ARIAState) -> Dict[str, Any]:
    """
    Node 1 — Trial Agent

    Fetches active clinical trials for the sponsor from ClinicalTrials.gov v2.
    Summarises phase distribution and conditions for downstream agents.
    Does not call the LLM — pure data retrieval.

    Self-skips if "trial" is not listed in execution_plan.agents.
    """
    planned_agents = state.get("execution_plan", {}).get("agents", ["trial", "intel", "fit"])
    if "trial" not in planned_agents:
        logger.info("[TrialAgent] Skipped by execution plan")
        return {}

    # Skip if data was pre-seeded from a previous run for the same company
    if state.get("trial_data", {}).get("trials"):
        logger.info("[TrialAgent] Skipped — trial data preserved from previous run")
        return {}

    company_name = state["company_name"]
    search_filters = state.get("search_filters", {})
    ta_filter    = search_filters.get("therapeutic_area") or None
    phase_filter = search_filters.get("phase") or None

    logger.info(
        "[TrialAgent] Fetching trials for: %s (TA=%s, phase=%s)",
        company_name, ta_filter, phase_filter,
    )

    try:
        trials = await fetch_trials(
            company_name,
            therapeutic_area=ta_filter,
            phase=phase_filter,
        )
    except Exception as exc:
        logger.error("[TrialAgent] Fetch failed: %s", exc)
        return {
            "trial_data": {"trials": [], "total_count": 0, "phases": {}, "conditions": []},
            "errors": [f"TrialAgent: {exc}"],
            "total_usage": [{"agent": "trial_agent", "input_tokens": 0, "output_tokens": 0}],
        }

    # Summarise phase distribution and deduplicated conditions
    phases: Dict[str, int] = {}
    conditions: List[str] = []
    for t in trials:
        phase = t.get("phase") or "UNKNOWN"
        phases[phase] = phases.get(phase, 0) + 1
        cond = t.get("condition")
        if cond and cond not in conditions:
            conditions.append(cond)

    trial_data = {
        "trials": trials,
        "total_count": len(trials),
        "phases": phases,
        "conditions": conditions[:20],  # cap to keep downstream prompts manageable
    }

    logger.info(
        "[TrialAgent] Found %d trials across %d phase(s) for %s",
        len(trials), len(phases), company_name,
    )

    return {
        "trial_data": trial_data,
        "total_usage": [{"agent": "trial_agent", "input_tokens": 0, "output_tokens": 0}],
    }
