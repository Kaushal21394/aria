from __future__ import annotations

import json
import logging
from typing import Any, AsyncIterator, Dict, List, Optional, Tuple

import anthropic

from ..config import settings
from ..models.schemas import SponsorBrief, TrialActivity, UsageLog

logger = logging.getLogger(__name__)

MAX_RETRIES = 1  # one self-correction attempt after a JSON parse failure

# ---------------------------------------------------------------------------
# System prompt — instructs Claude to act as a CRO BD analyst
# ---------------------------------------------------------------------------
SYSTEM_PROMPT = """You are a senior Business Development analyst at a global CRO (Contract Research Organisation).
Your job is to read raw sponsor data and produce a concise BD intelligence brief.

CRITICAL: Return ONLY a valid JSON object matching the schema below. No markdown fences, no explanation.

Schema:
{
  "company_overview": "2-3 sentence summary of the company, size, focus areas",
  "pipeline_summary": [
    {"phase": "PHASE2", "therapeutic_area": "Oncology", "trial_count": 5, "key_indications": ["NSCLC", "Breast"]}
  ],
  "trial_activity": {
    "total_active_trials": 12,
    "phases": {"PHASE1": 3, "PHASE2": 6, "PHASE3": 3},
    "therapeutic_areas": ["Oncology", "Rare Disease"],
    "geographic_spread": ["United States", "Europe", "Asia Pacific"]
  },
  "opportunity_signals": [
    "Strong Phase 2 oncology pipeline — likely needs CRO support for Phase 3 scale-up",
    "Multiple rare disease trials indicate specialised patient recruitment needs"
  ],
  "recommended_service_areas": [
    "Phase 2/3 Oncology Trial Management",
    "Rare Disease Patient Recruitment",
    "Biostatistics and Data Management"
  ]
}"""


def _strip_fences(text: str) -> str:
    """Remove markdown code fences Claude sometimes adds despite instructions."""
    text = text.strip()
    if text.startswith("```"):
        lines = text.splitlines()
        # drop opening fence line (```json or ```) and closing ``` line
        lines = [l for l in lines if not l.strip().startswith("```")]
        text = "\n".join(lines).strip()
    return text


def _parse_with_retry(
    client: anthropic.Anthropic,
    messages: List[Dict[str, Any]],
    raw_text: str,
) -> tuple[dict, int, int]:
    """
    Try to parse raw_text as JSON.
    On failure, send the broken output back to Claude with a correction prompt
    and try once more.

    Returns (parsed_dict, extra_input_tokens, extra_output_tokens).
    The token counts are non-zero only when a retry was needed.
    """
    text = _strip_fences(raw_text)
    try:
        return json.loads(text), 0, 0
    except json.JSONDecodeError as first_err:
        logger.warning("JSON parse failed on first attempt (%s) — retrying", first_err)

    # Self-correction: show Claude what it produced and ask it to fix it
    retry_messages = messages + [
        {"role": "assistant", "content": raw_text},
        {
            "role": "user",
            "content": (
                f"Your response was not valid JSON. Parse error: {first_err}\n"
                "Return ONLY the corrected JSON object. No explanation, no fences."
            ),
        },
    ]
    retry_response = client.messages.create(
        model=settings.aria_model,
        max_tokens=2000,
        system=SYSTEM_PROMPT,
        messages=retry_messages,
    )
    retry_text = _strip_fences(retry_response.content[0].text)
    parsed = json.loads(retry_text)  # let this raise if still broken
    logger.info("JSON parse succeeded after retry")
    return (
        parsed,
        retry_response.usage.input_tokens,
        retry_response.usage.output_tokens,
    )


def _build_user_prompt(
    company_name: str,
    trials: List[Dict[str, Any]],
    sec_data: Dict[str, Any],
    config: Optional[Dict[str, Any]] = None,
) -> str:
    trial_summary = []
    for t in trials[:30]:  # cap at 30 to control token usage
        trial_summary.append(
            f"- [{t['nct_id']}] {t['title']} | Phase: {t['phase']} | "
            f"Status: {t['status']} | Condition: {t['condition']}"
        )

    sec_summary = (
        f"Public company: {sec_data['is_public_company']} | "
        f"Recent SEC filings: {sec_data['total_filings_found']}"
    )

    # Append active filters so Claude focuses its analysis accordingly
    filter_note = ""
    if config:
        parts = []
        if config.get("therapeutic_area"):
            parts.append(f"therapeutic area = {config['therapeutic_area']}")
        if config.get("phase"):
            parts.append(f"trial phase = {config['phase']}")
        if parts:
            filter_note = f"\nActive filters (focus analysis on): {', '.join(parts)}"

    return f"""Company: {company_name}{filter_note}

Active/Recruiting Trials ({len(trials)} total):
{chr(10).join(trial_summary) if trial_summary else "No active trials found."}

SEC EDGAR data:
{sec_summary}

Generate the BD intelligence brief JSON."""


async def stream_brief_events(
    company_name: str,
    trials: List[Dict[str, Any]],
    sec_data: Dict[str, Any],
    config: Optional[Dict[str, Any]] = None,
) -> AsyncIterator[str]:
    """
    Async generator that yields Server-Sent Event strings.

    SSE format — each event is two lines:
        data: <json>\n\n

    Event types:
        {"type": "status",  "message": "..."}         — progress update
        {"type": "chunk",   "text": "..."}             — raw text fragment from Claude
        {"type": "done",    "brief": {...}, "usage": {...}}  — final parsed brief
        {"type": "error",   "message": "..."}          — failure mid-stream
    """
    def _sse(payload: dict) -> str:
        return f"data: {json.dumps(payload)}\n\n"

    async_client = anthropic.AsyncAnthropic(api_key=settings.anthropic_api_key)
    user_prompt = _build_user_prompt(company_name, trials, sec_data, config)
    first_message = [{"role": "user", "content": user_prompt}]

    full_text = ""
    extra_input = extra_output = 0

    try:
        async with async_client.messages.stream(
            model=settings.aria_model,
            max_tokens=2000,
            system=SYSTEM_PROMPT,
            messages=first_message,
        ) as stream:
            async for text_chunk in stream.text_stream:
                full_text += text_chunk
                yield _sse({"type": "chunk", "text": text_chunk})

            final = await stream.get_final_message()

        # Parse with retry — streaming doesn't support a second turn natively,
        # so we fall back to the sync client for the correction call if needed.
        try:
            parsed = json.loads(_strip_fences(full_text))
        except json.JSONDecodeError as first_err:
            logger.warning("Stream JSON parse failed (%s) — retrying via sync client", first_err)
            yield _sse({"type": "status", "message": "Correcting output format…"})
            sync_client = anthropic.Anthropic(api_key=settings.anthropic_api_key)
            parsed, extra_input, extra_output = _parse_with_retry(
                sync_client, first_message, full_text
            )

        trial_activity_data = parsed.get("trial_activity", {})
        trial_activity = TrialActivity(
            total_active_trials=len(trials),
            phases=trial_activity_data.get("phases", {}),
            therapeutic_areas=trial_activity_data.get("therapeutic_areas", []),
            geographic_spread=trial_activity_data.get("geographic_spread", []),
        )
        brief = SponsorBrief(
            company_name=company_name,
            company_overview=parsed["company_overview"],
            pipeline_summary=parsed.get("pipeline_summary", []),
            trial_activity=trial_activity,
            opportunity_signals=parsed.get("opportunity_signals", []),
            recommended_service_areas=parsed.get("recommended_service_areas", []),
        )
        # Add any retry tokens to the total so the UI shows true cost
        usage = UsageLog(
            model=settings.aria_model,
            input_tokens=final.usage.input_tokens + extra_input,
            output_tokens=final.usage.output_tokens + extra_output,
        )

        yield _sse({
            "type": "done",
            "brief": brief.model_dump(),
            "raw_trial_count": len(trials),
            "sec_filings_found": sec_data.get("total_filings_found", 0),
            "usage": usage.model_dump(),
        })

    except json.JSONDecodeError as exc:
        yield _sse({"type": "error", "message": f"Failed to parse model response as JSON: {exc}"})
    except Exception as exc:
        yield _sse({"type": "error", "message": str(exc)})


def generate_brief(
    company_name: str,
    trials: List[Dict[str, Any]],
    sec_data: Dict[str, Any],
    config: Optional[Dict[str, Any]] = None,
) -> Tuple[SponsorBrief, UsageLog]:
    """
    Call Anthropic API to produce a structured SponsorBrief.
    Returns (brief, usage_log) so callers can track token spend.
    """
    client = anthropic.Anthropic(api_key=settings.anthropic_api_key)
    messages = [{"role": "user", "content": _build_user_prompt(company_name, trials, sec_data, config)}]

    response = client.messages.create(
        model=settings.aria_model,
        max_tokens=2000,
        system=SYSTEM_PROMPT,
        messages=messages,
    )

    raw_text = response.content[0].text
    parsed, extra_input, extra_output = _parse_with_retry(client, messages, raw_text)

    trial_activity_data = parsed.get("trial_activity", {})
    trial_activity = TrialActivity(
        total_active_trials=len(trials),  # use real count, not hallucinated
        phases=trial_activity_data.get("phases", {}),
        therapeutic_areas=trial_activity_data.get("therapeutic_areas", []),
        geographic_spread=trial_activity_data.get("geographic_spread", []),
    )

    brief = SponsorBrief(
        company_name=company_name,
        company_overview=parsed["company_overview"],
        pipeline_summary=parsed.get("pipeline_summary", []),
        trial_activity=trial_activity,
        opportunity_signals=parsed.get("opportunity_signals", []),
        recommended_service_areas=parsed.get("recommended_service_areas", []),
    )

    usage = UsageLog(
        model=settings.aria_model,
        input_tokens=response.usage.input_tokens + extra_input,
        output_tokens=response.usage.output_tokens + extra_output,
    )

    return brief, usage
