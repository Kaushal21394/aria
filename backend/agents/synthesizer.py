from __future__ import annotations

import asyncio
import json
import logging
from typing import Any, Dict

import anthropic

from ..config import settings
from ..rag.retrieval import format_rag_context, retrieve_proposals
from ._utils import with_backoff
from .state import ARIAState
from .stream_context import get_stream_queue

logger = logging.getLogger(__name__)

# ── System prompts per output format ─────────────────────────────────────────

_SYSTEM_PROMPTS: Dict[str, str] = {
    "outreach_email": """\
You are a CRO BD director writing personalised cold outreach emails to pharma/biotech sponsors.

Write a concise, professional email (250–350 words). The email must:
1. Open with a specific reference to one of their active programmes (phase + indication)
2. Demonstrate understanding of their therapeutic strategy
3. Reference a specific relevant past study we have run (from the Past Proposals context) — cite it concretely
4. Propose a specific 30-minute discovery call as the only call-to-action

Tone: warm but direct. No generic CRO boilerplate. No subject line. Plain email body only.""",

    "competitive_brief": """\
You are a pharma BD analyst producing a competitive landscape brief.

Write a structured brief (400–600 words) with clear section headers covering:
1. Sponsor Overview — pipeline size, therapeutic focus, development stage
2. Competitive Positioning — where they sit relative to peers in their key TAs
3. BD Opportunity Landscape — where CRO partnerships are likely, relevant service areas
4. Risk Flags — signals suggesting lower fit or timing concerns
5. Recommended Approach — how to position and when to engage

Be analytical, not promotional. Draw conclusions from the data provided.""",

    "pipeline_summary": """\
You are a pharma intelligence analyst summarising a sponsor's pipeline.

Write a focused pipeline summary (300–500 words) covering:
1. Pipeline Snapshot — total trials, phase distribution, key indications
2. Therapeutic Strategy — what the data reveals about their R&D priorities
3. Momentum Signals — recent starts, completions, phase transitions
4. CRO Opportunity Flags — where outsourcing demand is likely to emerge

Be data-driven. Cite specific trial phases and indications where possible.""",

    "account_snapshot": """\
You are a pharma BD analyst producing a quick executive account snapshot.

Write a concise snapshot (150–250 words) covering:
1. Who They Are — company type, size signals, therapeutic focus
2. What They're Doing — pipeline activity summary in plain language
3. Why They Matter — BD relevance and partnership potential

This is a quick-read for a BD rep preparing for a call. Be crisp and direct.""",
}

# ── MCP tools (outreach_email only) ──────────────────────────────────────────

_MCP_TOOLS = [
    {
        "name": "draft_gmail_email",
        "description": "Save the outreach email as a Gmail draft for the BD rep to review and send.",
        "input_schema": {
            "type": "object",
            "properties": {
                "to":      {"type": "string", "description": "Recipient — use 'bd@<company>.com' placeholder"},
                "subject": {"type": "string", "description": "Subject line (max 80 chars)"},
                "body":    {"type": "string", "description": "Full email body (no HTML)"},
            },
            "required": ["to", "subject", "body"],
        },
    },
    {
        "name": "create_calendar_event",
        "description": "Schedule a 30-minute discovery call placeholder in Google Calendar.",
        "input_schema": {
            "type": "object",
            "properties": {
                "title":            {"type": "string"},
                "proposed_date":    {"type": "string", "description": "YYYY-MM-DD, ~2 weeks out"},
                "duration_minutes": {"type": "integer"},
                "attendees":        {"type": "array", "items": {"type": "string"}},
            },
            "required": ["title", "proposed_date", "duration_minutes"],
        },
    },
]

_MCP_SYSTEM = (
    "You are an ARIA automation agent. Given the drafted BD outreach email, "
    "call BOTH tools: (1) save it as a Gmail draft and (2) schedule a 30-minute "
    "discovery call approximately 2 weeks from today. Use placeholder emails. "
    "Call both tools — no commentary."
)


def _handle_draft_gmail(inputs: dict) -> dict:
    logger.info("[MCP/Gmail] Draft saved — to=%s subject=%s", inputs["to"], inputs["subject"])
    return {
        "status": "ok",
        "draft_id": "gmail_draft_aria_001",
        "to": inputs["to"],
        "subject": inputs["subject"],
        "preview": inputs["body"][:120] + "…",
        "message": "Draft saved to Gmail. Open Gmail to review and send.",
    }


def _handle_create_calendar(inputs: dict) -> dict:
    logger.info("[MCP/Calendar] Event created — %s on %s", inputs["title"], inputs["proposed_date"])
    return {
        "status": "ok",
        "event_id": "gcal_aria_001",
        "title": inputs["title"],
        "date": inputs["proposed_date"],
        "duration": inputs.get("duration_minutes", 30),
        "meet_link": "https://meet.google.com/aria-discovery-placeholder",
        "message": f"Discovery call blocked on {inputs['proposed_date']}. Share the Meet link with the sponsor.",
    }


_MCP_HANDLERS = {
    "draft_gmail_email": _handle_draft_gmail,
    "create_calendar_event": _handle_create_calendar,
}


async def _run_mcp_actions(
    client: anthropic.AsyncAnthropic, synthesis: str, company_name: str
) -> list[dict]:
    messages = [{
        "role": "user",
        "content": f"Company: {company_name}\n\nDrafted email:\n{synthesis}\n\nNow call both tools.",
    }]
    mcp_actions = []

    for _ in range(4):
        response = await with_backoff(
            client.messages.create,
            model=settings.aria_model,
            max_tokens=400,
            system=_MCP_SYSTEM,
            tools=_MCP_TOOLS,
            messages=messages,
        )
        if response.stop_reason == "end_turn":
            break
        if response.stop_reason == "tool_use":
            messages.append({"role": "assistant", "content": response.content})
            tool_results = []
            for block in response.content:
                if block.type != "tool_use":
                    continue
                handler = _MCP_HANDLERS.get(block.name)
                result = handler(block.input) if handler else {"error": f"Unknown tool: {block.name}"}
                mcp_actions.append({"tool": block.name, "input": block.input, "result": result})
                tool_results.append({
                    "type": "tool_result",
                    "tool_use_id": block.id,
                    "content": json.dumps(result),
                })
            messages.append({"role": "user", "content": tool_results})

    return mcp_actions


# ── Prompt builder ────────────────────────────────────────────────────────────

_TA_MAP = {
    "oncology": "oncology", "cancer": "oncology", "tumor": "oncology",
    "neurology": "neurology", "alzheimer": "neurology", "parkinson": "neurology",
    "cardiology": "cardiology", "cardiac": "cardiology", "heart": "cardiology",
    "metabolic": "metabolic", "diabetes": "metabolic", "obesity": "metabolic",
    "respiratory": "respiratory", "copd": "respiratory", "asthma": "respiratory",
    "immunology": "immunology", "rheumatoid": "immunology", "lupus": "immunology",
    "rare": "rare_disease", "genetic": "rare_disease",
    "infectious": "infectious_disease", "vaccine": "infectious_disease",
}


def _build_prompt(state: ARIAState, output_format: str, rag_context_str: str = "") -> str:
    company_name = state["company_name"]
    user_goal = state.get("user_goal", "")
    trial_data = state.get("trial_data", {})
    intel_data = state.get("intel_data", {})
    fit_score = state.get("fit_score", {})

    sections = [f"Company: {company_name}"]
    if user_goal:
        sections.append(f"User goal: {user_goal}")

    if trial_data:
        conditions = trial_data.get("conditions", [])[:5]
        sections.append(
            f"\nTrial Activity:"
            f"\n- Active trials: {trial_data.get('total_count', 0)}"
            f"\n- Phases: {trial_data.get('phases', {})}"
            f"\n- Key conditions: {', '.join(conditions) if conditions else 'not available'}"
        )

    if intel_data:
        key_signals = intel_data.get("key_signals", [])[:4]
        pipeline_updates = intel_data.get("pipeline_updates", [])[:3]
        sections.append(
            f"\nMarket Intelligence:"
            f"\n- BD signals: {key_signals if key_signals else 'not available'}"
            f"\n- Pipeline updates: {pipeline_updates if pipeline_updates else 'not available'}"
        )

    if fit_score and fit_score.get("total_score"):
        dimensions = fit_score.get("dimensions", {})
        if dimensions:
            top_dim_key, top_dim_val = max(dimensions.items(), key=lambda x: x[1].get("score", 0))
            top_dim_label = top_dim_key.replace("_", " ").title()
            top_dim_rationale = top_dim_val.get("rationale", "")
        else:
            top_dim_label, top_dim_rationale = "capabilities", ""
        sections.append(
            f"\nFit Assessment:"
            f"\n- CRO fit score: {fit_score.get('total_score', 0)}/100"
            f"\n- Strongest fit: {top_dim_label} — {top_dim_rationale}"
            f"\n- Summary: {fit_score.get('summary', '')}"
        )

    if output_format == "outreach_email" and rag_context_str:
        sections.append(
            f"\nPast Proposals — cite one specifically in the email:\n{rag_context_str}"
        )

    sections.append(f"\nNow produce the {output_format.replace('_', ' ')}.")
    return "\n".join(sections)


# ── Main node ─────────────────────────────────────────────────────────────────

async def synthesizer_node(state: ARIAState) -> Dict[str, Any]:
    """
    Final node — Synthesizer

    Produces freeform output shaped by execution_plan.output_format and the
    user's original goal. Behaviour per format:
      - outreach_email:    RAG retrieval + MCP Gmail/Calendar actions
      - competitive_brief: structured landscape analysis (no RAG/MCP)
      - pipeline_summary:  pipeline-focused summary (no RAG/MCP)
      - account_snapshot:  quick exec summary (no RAG/MCP)
    """
    company_name = state["company_name"]
    execution_plan = state.get("execution_plan", {})
    output_format = execution_plan.get("output_format", "outreach_email")

    logger.info("[Synthesizer] Producing '%s' for: %s", output_format, company_name)

    system_prompt = _SYSTEM_PROMPTS.get(output_format, _SYSTEM_PROMPTS["account_snapshot"])
    rag_hits: list = []
    rag_context_str = ""

    # RAG retrieval — outreach_email only
    if output_format == "outreach_email":
        trial_data = state.get("trial_data", {})
        search_filters = state.get("search_filters", {})
        top_conditions = trial_data.get("conditions", [])[:3]
        ta_raw = top_conditions[0].lower() if top_conditions else ""

        ta_filter = search_filters.get("therapeutic_area") or next(
            (corpus_ta for keyword, corpus_ta in _TA_MAP.items() if keyword in ta_raw), None
        )
        rag_query = f"{company_name} {ta_raw} CRO clinical trial proposal"
        logger.info("[Synthesizer] RAG query: '%s' (TA filter: %s)", rag_query, ta_filter)

        try:
            rag_hits = retrieve_proposals(
                query=rag_query,
                therapeutic_area=ta_filter,
                phase=search_filters.get("phase") or None,
                geography=search_filters.get("geography") or None,
                top_k=3,
            )
            rag_context_str = format_rag_context(rag_hits)
        except Exception as exc:
            logger.warning("[Synthesizer] RAG retrieval failed: %s — proceeding without context", exc)
            rag_context_str = "No relevant past proposals available."

    prompt = _build_prompt(state, output_format, rag_context_str)
    await asyncio.sleep(5)   # brief pause to stay within 30K tokens/min rate limit
    client = anthropic.AsyncAnthropic(api_key=settings.anthropic_api_key)

    try:
        queue = get_stream_queue()
        synthesis = ""
        usage: Dict[str, Any] = {"agent": "synthesizer", "input_tokens": 0, "output_tokens": 0}

        async with client.messages.stream(
            model=settings.aria_model,
            max_tokens=800,
            system=system_prompt,
            messages=[{"role": "user", "content": prompt}],
        ) as stream:
            async for text_chunk in stream.text_stream:
                synthesis += text_chunk
                if queue is not None:
                    await queue.put({"type": "synthesis_chunk", "text": text_chunk})

            final_msg = await stream.get_final_message()
            usage = {
                "agent": "synthesizer",
                "input_tokens": final_msg.usage.input_tokens,
                "output_tokens": final_msg.usage.output_tokens,
            }

        # MCP actions — outreach_email only
        mcp_actions: list = []
        if output_format == "outreach_email":
            logger.info("[Synthesizer] Running MCP tool loop for %s…", company_name)
            try:
                mcp_actions = await _run_mcp_actions(client, synthesis, company_name)
            except Exception as mcp_exc:
                logger.warning("[Synthesizer] MCP loop failed (non-fatal): %s", mcp_exc)

        return {
            "synthesis":   synthesis,
            "rag_context": rag_hits,
            "mcp_actions": mcp_actions,
            "total_usage": [usage],
        }

    except Exception as exc:
        logger.error("[Synthesizer] Failed: %s", exc)
        return {
            "synthesis":   "",
            "rag_context": [],
            "mcp_actions": [],
            "errors":      [f"Synthesizer: {exc}"],
            "total_usage": [{"agent": "synthesizer", "input_tokens": 0, "output_tokens": 0}],
        }
