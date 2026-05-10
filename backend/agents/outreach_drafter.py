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

_PRE_CALL_DELAY = 20

logger = logging.getLogger(__name__)

OUTREACH_SYSTEM = """You are a CRO BD director writing personalised cold outreach emails to pharma/biotech sponsors.

Write a concise, professional email (250–350 words). The email must:
1. Open with a specific reference to one of their active programmes (phase + indication)
2. Demonstrate understanding of their therapeutic strategy
3. Reference a specific relevant past study we have run (from the Past Proposals context) — cite it concretely
4. Propose a specific 30-minute discovery call as the only call-to-action

Tone: warm but direct. No generic CRO boilerplate. No subject line. Plain email body only."""

# ── Phase 4: MCP tool definitions (real Anthropic tool_use format) ─────────
# These mirror what a live Gmail MCP + Calendar MCP server would expose.
# The handlers below simulate the MCP server responses — in production
# they would be HTTP calls to the respective MCP endpoints.

_MCP_TOOLS = [
    {
        "name": "draft_gmail_email",
        "description": (
            "Save the outreach email as a Gmail draft so the BD rep can review "
            "and send it from their own inbox. Call this after composing the email."
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "to":      {"type": "string",  "description": "Recipient email — use 'bd@<company>.com' placeholder"},
                "subject": {"type": "string",  "description": "Email subject line (max 80 chars)"},
                "body":    {"type": "string",  "description": "Full email body text (no HTML)"},
            },
            "required": ["to", "subject", "body"],
        },
    },
    {
        "name": "create_calendar_event",
        "description": (
            "Schedule a 30-minute discovery call placeholder in Google Calendar "
            "so the BD rep can share the invite link with the sponsor."
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "title":            {"type": "string",  "description": "Event title"},
                "proposed_date":    {"type": "string",  "description": "Proposed date as YYYY-MM-DD (suggest ~2 weeks out)"},
                "duration_minutes": {"type": "integer", "description": "Duration (always 30)"},
                "attendees":        {
                    "type": "array",
                    "items": {"type": "string"},
                    "description": "List of attendee email placeholders",
                },
            },
            "required": ["title", "proposed_date", "duration_minutes"],
        },
    },
]

_MCP_SYSTEM = (
    "You are an ARIA automation agent. Given the drafted BD outreach email below, "
    "call BOTH available tools to (1) save it as a Gmail draft and (2) schedule a "
    "30-minute discovery call in Google Calendar approximately 2 weeks from today. "
    "Use placeholder email addresses (bd@<company>.com style). "
    "Call both tools — do not explain or add commentary."
)


# ── Simulated MCP server handlers ─────────────────────────────────────────
# In production: replace with `httpx.AsyncClient().post(MCP_SERVER_URL, ...)`.

def _handle_draft_gmail(inputs: dict) -> dict:
    """Simulate: POST https://gmail-mcp.example.com/drafts"""
    logger.info("[MCP/Gmail] Draft saved — to=%s subject=%s", inputs["to"], inputs["subject"])
    return {
        "status":   "ok",
        "draft_id": "gmail_draft_aria_001",
        "to":       inputs["to"],
        "subject":  inputs["subject"],
        "preview":  inputs["body"][:120] + "…",
        "message":  "Draft saved to Gmail. Open Gmail to review and send.",
    }


def _handle_create_calendar(inputs: dict) -> dict:
    """Simulate: POST https://calendar-mcp.example.com/events"""
    logger.info("[MCP/Calendar] Event created — %s on %s", inputs["title"], inputs["proposed_date"])
    return {
        "status":    "ok",
        "event_id":  "gcal_aria_001",
        "title":     inputs["title"],
        "date":      inputs["proposed_date"],
        "duration":  inputs.get("duration_minutes", 30),
        "attendees": inputs.get("attendees", []),
        "meet_link": "https://meet.google.com/aria-discovery-placeholder",
        "message":   f"Discovery call blocked on {inputs['proposed_date']}. Share the Meet link with the sponsor.",
    }


_MCP_HANDLERS = {
    "draft_gmail_email":    _handle_draft_gmail,
    "create_calendar_event": _handle_create_calendar,
}


async def _run_mcp_actions(client: anthropic.AsyncAnthropic, outreach_draft: str, company_name: str) -> list[dict]:
    """
    Phase 4 — MCP ReAct loop.

    Makes one tool_use call asking Claude to:
      (a) save the drafted email to Gmail via draft_gmail_email
      (b) schedule a discovery call via create_calendar_event

    Handles both tool calls and returns a list of MCP action results
    suitable for storing in ARIAState.mcp_actions.
    """
    messages = [
        {
            "role": "user",
            "content": (
                f"Company: {company_name}\n\n"
                f"Drafted email:\n{outreach_draft}\n\n"
                "Now call both tools."
            ),
        }
    ]

    mcp_actions = []
    max_iter = 4  # safety cap on the tool-use loop

    for _ in range(max_iter):
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
                    "type":        "tool_result",
                    "tool_use_id": block.id,
                    "content":     json.dumps(result),
                })

            messages.append({"role": "user", "content": tool_results})

    return mcp_actions


# ── Main node ──────────────────────────────────────────────────────────────

async def outreach_drafter_node(state: ARIAState) -> Dict[str, Any]:
    """
    Node 4 — Outreach Drafter (Phase 4 upgrade)

    Phase 3: RAG retrieval + personalised BD email
    Phase 4: After drafting, runs a MCP ReAct loop to:
      - Save the email as a Gmail draft (simulated)
      - Schedule a 30-min discovery call in Google Calendar (simulated)
    Results are stored in state.mcp_actions and surfaced in the UI.
    """
    company_name = state["company_name"]
    trial_data = state.get("trial_data", {})
    intel_data = state.get("intel_data", {})
    fit_score = state.get("fit_score", {})

    # ── RAG retrieval ─────────────────────────────────────────────────────
    search_filters = state.get("search_filters", {})
    top_conditions = trial_data.get("conditions", [])[:3]
    ta_raw = top_conditions[0].lower() if top_conditions else ""

    if search_filters.get("therapeutic_area"):
        ta_filter = search_filters["therapeutic_area"]
    else:
        TA_MAP = {
            "oncology": "oncology", "cancer": "oncology", "tumor": "oncology",
            "neurology": "neurology", "alzheimer": "neurology", "parkinson": "neurology",
            "cardiology": "cardiology", "cardiac": "cardiology", "heart": "cardiology",
            "metabolic": "metabolic", "diabetes": "metabolic", "obesity": "metabolic",
            "respiratory": "respiratory", "copd": "respiratory", "asthma": "respiratory",
            "immunology": "immunology", "rheumatoid": "immunology", "lupus": "immunology",
            "rare": "rare_disease", "genetic": "rare_disease",
            "infectious": "infectious_disease", "vaccine": "infectious_disease",
        }
        ta_filter = next(
            (corpus_ta for keyword, corpus_ta in TA_MAP.items() if keyword in ta_raw),
            None,
        )

    geo_filter = search_filters.get("geography") or None
    phase_filter = search_filters.get("phase") or None

    rag_query = f"{company_name} {ta_raw} CRO clinical trial proposal"
    logger.info("[OutreachDrafter] RAG query: '%s' (TA filter: %s)", rag_query, ta_filter)

    try:
        rag_hits = retrieve_proposals(
            query=rag_query,
            therapeutic_area=ta_filter,
            phase=phase_filter,
            geography=geo_filter,
            top_k=3,
        )
        rag_context_str = format_rag_context(rag_hits)
    except Exception as exc:
        logger.warning("[OutreachDrafter] RAG retrieval failed: %s. Proceeding without context.", exc)
        rag_hits = []
        rag_context_str = "No relevant past proposals available."

    # ── Build prompt ──────────────────────────────────────────────────────
    logger.info("[OutreachDrafter] Waiting %ds before API call to avoid rate limit…", _PRE_CALL_DELAY)
    await asyncio.sleep(_PRE_CALL_DELAY)
    logger.info("[OutreachDrafter] Drafting email for: %s", company_name)

    key_signals = intel_data.get("key_signals", [])[:3]
    pipeline_updates = intel_data.get("pipeline_updates", [])[:3]
    total_score = fit_score.get("total_score", 0)

    dimensions = fit_score.get("dimensions", {})
    if dimensions:
        top_dim_key, top_dim_val = max(
            dimensions.items(), key=lambda x: x[1].get("score", 0)
        )
        top_dim_label = top_dim_key.replace("_", " ").title()
        top_dim_rationale = top_dim_val.get("rationale", "")
    else:
        top_dim_label, top_dim_rationale = "capabilities", ""

    prompt = f"""Write a BD outreach email to clinical operations or R&D leadership at {company_name}.

Sponsor profile:
- Active trials: {trial_data.get('total_count', 0)} (phases: {trial_data.get('phases', {})})
- Key therapeutic focus: {', '.join(top_conditions) if top_conditions else 'not available'}
- CRO fit score: {total_score}/100
- Strongest fit area: {top_dim_label} — {top_dim_rationale}

Recent intelligence signals:
{chr(10).join(f'- {s}' for s in key_signals) if key_signals else '- No recent signals available'}

Pipeline updates:
{chr(10).join(f'- {u}' for u in pipeline_updates) if pipeline_updates else '- No recent updates available'}

Past Proposals — relevant past studies we have run (cite one specifically in the email):
{rag_context_str}

Write the email body now."""

    client = anthropic.AsyncAnthropic(api_key=settings.anthropic_api_key)

    try:
        # ── Stream the email draft token-by-token ─────────────────────────
        # If the orchestrator set a stream_queue in the current context,
        # pipe each text chunk into it as an "email_chunk" event so the
        # frontend can render the email as it's generated.
        queue = get_stream_queue()
        outreach_draft = ""
        draft_usage = {"agent": "outreach_drafter", "input_tokens": 0, "output_tokens": 0}

        async with client.messages.stream(
            model=settings.aria_model,
            max_tokens=800,
            system=OUTREACH_SYSTEM,
            messages=[{"role": "user", "content": prompt}],
        ) as stream:
            async for text_chunk in stream.text_stream:
                outreach_draft += text_chunk
                if queue is not None:
                    await queue.put({"type": "email_chunk", "text": text_chunk})

            final_msg = await stream.get_final_message()
            draft_usage = {
                "agent":        "outreach_drafter",
                "input_tokens":  final_msg.usage.input_tokens,
                "output_tokens": final_msg.usage.output_tokens,
            }

        # ── Phase 4: MCP actions ──────────────────────────────────────────
        logger.info("[OutreachDrafter] Running MCP tool loop for %s…", company_name)
        try:
            mcp_actions = await _run_mcp_actions(client, outreach_draft, company_name)
        except Exception as mcp_exc:
            logger.warning("[OutreachDrafter] MCP loop failed (non-fatal): %s", mcp_exc)
            mcp_actions = []

        return {
            "outreach_draft": outreach_draft,
            "rag_context":    rag_hits,
            "mcp_actions":    mcp_actions,
            "total_usage": [draft_usage],
        }

    except Exception as exc:
        logger.error("[OutreachDrafter] Failed: %s", exc)
        return {
            "outreach_draft": "",
            "rag_context":    [],
            "mcp_actions":    [],
            "errors":         [f"OutreachDrafter: {exc}"],
            "total_usage":    [{"agent": "outreach_drafter", "input_tokens": 0, "output_tokens": 0}],
        }
