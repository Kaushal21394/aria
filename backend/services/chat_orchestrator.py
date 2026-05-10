from __future__ import annotations

"""
Chat Orchestrator — Phase 5

Claude acts as the routing brain. It has two tools:
  • run_research(company_name, filters?)  → full 4-agent LangGraph pipeline
  • generate_brief(company_name, filters?) → Phase 1 single-call brief

When Claude decides a tool is needed it emits a tool_use block; the orchestrator
invokes the real function, streams live agent progress back to the client via an
asyncio.Queue, then feeds the result back to Claude for a final conversational reply.

SSE event shapes yielded by orchestrate():
  {"type": "thinking"}                              — orchestrator decided to call a tool
  {"type": "tool_start",  "tool": str, "input": {}} — tool invocation begins
  {"type": "agent_step",  "agent": str, "message": str} — live progress inside run_research
  {"type": "tool_done",   "tool": str, "result_type": "research"|"brief", "result": {}}
  {"type": "text_chunk",  "text": str}              — streaming assistant commentary
  {"type": "done",        "text": str, "result_type": str|None, "result": {}|None}
  {"type": "error",       "message": str}
"""

import asyncio
import json
import logging
from typing import Any, AsyncIterator, Dict, List, Optional

import anthropic

from ..agents.graph import build_aria_graph
from ..agents.stream_context import stream_queue_var
from ..config import settings
from ..services.clinical_trials import fetch_trials
from ..services.sec_edgar import fetch_sec_filings
from ..services.brief_generator import generate_brief as _generate_brief

logger = logging.getLogger(__name__)

# ── Orchestrator system prompt ─────────────────────────────────────────────

SYSTEM = """\
You are ARIA, an AI-powered CRO (Contract Research Organisation) Business Development assistant.
You help BD teams research pharma/biotech sponsors, score their fit, and craft outreach emails.

You have two tools:
• run_research   — runs the full 4-agent pipeline (trial data → intel → fit score → outreach email).
                   Use this when the user wants a deep analysis or outreach email for a company.
• generate_brief — produces a quick single-call sponsor intelligence brief.
                   Use this for fast lookups or when the user asks for a "brief" or "overview".

Guidelines:
- If the user names a company and asks for research, analysis, score, or outreach → run_research.
- If the user asks for a quick overview, summary, or brief → generate_brief.
- If the user asks a follow-up question about a previous result, answer from context — do NOT re-run tools.
- Be concise. After a tool result, write 2-4 sentences of commentary, then stop.
- Never invent clinical trial data. Only comment on what the tools return.
"""

# ── Tool schemas (Anthropic tool_use format) ──────────────────────────────

TOOLS: List[Dict] = [
    {
        "name": "run_research",
        "description": (
            "Run the full ARIA 4-agent research pipeline for a pharma/biotech company. "
            "Returns trial data, market intel, a CRO fit score, and a personalised BD outreach email."
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "company_name": {
                    "type": "string",
                    "description": "The pharma/biotech company name to research.",
                },
                "therapeutic_area": {
                    "type": "string",
                    "description": "Optional filter, e.g. 'oncology', 'neurology'.",
                },
                "phase": {
                    "type": "string",
                    "description": "Optional trial phase filter, e.g. 'Phase II'.",
                },
                "geography": {
                    "type": "string",
                    "description": "Optional geography filter, e.g. 'north_america'.",
                },
            },
            "required": ["company_name"],
        },
    },
    {
        "name": "generate_brief",
        "description": (
            "Generate a quick sponsor intelligence brief for a pharma/biotech company. "
            "Faster than run_research. Returns company overview, pipeline summary, and opportunity signals."
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "company_name": {
                    "type": "string",
                    "description": "The pharma/biotech company name.",
                },
                "therapeutic_area": {"type": "string"},
                "phase":            {"type": "string"},
            },
            "required": ["company_name"],
        },
    },
]

# ── Tool handlers ──────────────────────────────────────────────────────────

AGENT_MESSAGES = {
    "trial_agent":      "Fetching clinical trial data from ClinicalTrials.gov…",
    "intel_agent":      "Gathering market intelligence…",
    "fit_scorer":       "Scoring CRO fit across 5 dimensions…",
    "outreach_drafter": "Drafting BD outreach email + MCP actions…",
}


async def _handle_run_research(
    inputs: Dict[str, Any],
    org_id: str,
    user_id: str,
    queue: asyncio.Queue,
) -> Dict[str, Any]:
    """
    Invoke the LangGraph pipeline, pushing events into queue:
      - "agent_step" events as each node completes
      - "email_chunk" events as the outreach drafter streams the email text
        (via the stream_queue_var ContextVar set below)
    """
    company_name = inputs["company_name"]
    filters = {
        k: inputs[k]
        for k in ("therapeutic_area", "phase", "geography")
        if inputs.get(k)
    }

    graph = build_aria_graph()
    initial_state = {
        "company_name":   company_name,
        "org_id":         org_id,
        "user_id":        user_id,
        "search_filters": filters,
        "trial_data":     {},
        "intel_data":     {},
        "fit_score":      {},
        "rag_context":    [],
        "outreach_draft": "",
        "mcp_actions":    [],
        "errors":         [],
        "total_usage":    [],
    }

    accumulated: Dict[str, Any] = {**initial_state, "errors": [], "total_usage": []}

    # Set the ContextVar so the outreach_drafter node can pipe email
    # tokens into the same queue without us passing it through LangGraph state.
    ctx_token = stream_queue_var.set(queue)
    try:
        async for chunk in graph.astream(initial_state, stream_mode="updates"):
            for node_name, updates in chunk.items():
                for key, value in updates.items():
                    if key in ("errors", "total_usage"):
                        accumulated[key] = accumulated.get(key, []) + (value or [])
                    else:
                        accumulated[key] = value
                await queue.put({
                    "type":    "agent_step",
                    "agent":   node_name,
                    "message": AGENT_MESSAGES.get(node_name, f"{node_name} complete"),
                })
    finally:
        stream_queue_var.reset(ctx_token)

    return {
        "company_name":   company_name,
        "trial_data":     accumulated.get("trial_data", {}),
        "intel_data":     accumulated.get("intel_data", {}),
        "fit_score":      accumulated.get("fit_score", {}),
        "rag_context":    accumulated.get("rag_context", []),
        "outreach_draft": accumulated.get("outreach_draft", ""),
        "mcp_actions":    accumulated.get("mcp_actions", []),
        "errors":         accumulated.get("errors", []),
        "total_usage":    accumulated.get("total_usage", []),
    }


async def _handle_generate_brief(inputs: Dict[str, Any]) -> Dict[str, Any]:
    """Invoke Phase 1 brief generation."""
    company_name = inputs["company_name"]
    ta   = inputs.get("therapeutic_area")
    phase = inputs.get("phase")

    trials, sec_data = await asyncio.gather(
        fetch_trials(company_name, therapeutic_area=ta, phase=phase),
        fetch_sec_filings(company_name),
    )
    brief, usage = _generate_brief(company_name, trials, sec_data,
                                   {"therapeutic_area": ta, "phase": phase} if (ta or phase) else None)
    return {
        "company_name":    company_name,
        "brief":           brief.model_dump(),
        "raw_trial_count": len(trials),
        "sec_filings_found": sec_data.get("total_filings_found", 0),
        "usage":           usage.model_dump(),
    }


# ── Main orchestrate generator ─────────────────────────────────────────────

async def orchestrate(
    user_message: str,
    history: List[Dict[str, Any]],
    org_id: str,
    user_id: str,
) -> AsyncIterator[Dict[str, Any]]:
    """
    Main chat loop. Yields SSE-ready dicts.

    history: list of {"role": "user"|"assistant", "content": str} dicts
             representing prior turns (loaded from DB).
    """
    client = anthropic.AsyncAnthropic(api_key=settings.anthropic_api_key)

    # Build message list: history + new user turn
    messages = [
        {"role": m["role"], "content": m["content"]}
        for m in history
    ] + [{"role": "user", "content": user_message}]

    # Track what we accumulate for the final "done" event
    final_text        = ""
    final_result_type: Optional[str] = None
    final_result:      Optional[Dict] = None

    max_iterations = 6  # safety cap on the tool-use loop

    for _ in range(max_iterations):
        # ── Peek: does the model want to use a tool or reply in text? ──────
        # We need tool definitions for routing, but streaming + tools in the
        # same call works fine — Anthropic streams tool_use blocks too.
        # Use stream() for the final reply pass; use create() for tool passes
        # so we can inspect stop_reason before committing to streaming.

        # First check with create() — fast, gives us stop_reason upfront
        probe = await client.messages.create(
            model=settings.aria_model,
            max_tokens=1024,
            system=SYSTEM,
            tools=TOOLS,
            messages=messages,
        )

        # ── Pure text reply — re-run with stream() for real token delivery ─
        if probe.stop_reason == "end_turn":
            final_text = ""
            async with client.messages.stream(
                model=settings.aria_model,
                max_tokens=1024,
                system=SYSTEM,
                # No tools needed — we already know this is a text reply
                messages=messages,
            ) as stream:
                async for text_chunk in stream.text_stream:
                    final_text += text_chunk
                    yield {"type": "text_chunk", "text": text_chunk}
            break

        # ── Tool use ──────────────────────────────────────────────────────
        if probe.stop_reason == "tool_use":
            yield {"type": "thinking"}

            # Append Claude's response (with tool_use blocks) to history
            messages.append({"role": "assistant", "content": probe.content})

            tool_results = []

            for block in probe.content:
                if block.type != "tool_use":
                    continue

                tool_name   = block.name
                tool_inputs = block.input

                yield {"type": "tool_start", "tool": tool_name, "input": tool_inputs}

                # Run tool — research uses a queue for live progress events
                try:
                    if tool_name == "run_research":
                        queue: asyncio.Queue = asyncio.Queue()

                        # Run the graph in a background task so we can drain
                        # the queue (agent step events) while it executes.
                        async def _research_task(q=queue):
                            result = await _handle_run_research(tool_inputs, org_id, user_id, q)
                            await q.put({"type": "__done__", "result": result})

                        task = asyncio.create_task(_research_task())

                        result = None
                        while True:
                            event = await queue.get()
                            if event.get("type") == "__done__":
                                result = event["result"]
                                break
                            yield event  # agent_step events

                        await task
                        final_result_type = "research"
                        final_result      = result
                        result_summary    = (
                            f"Research complete. Fit score: {result.get('fit_score', {}).get('total_score', 'N/A')}/100. "
                            f"Active trials: {result.get('trial_data', {}).get('total_count', 'N/A')}."
                        )

                    elif tool_name == "generate_brief":
                        result = await _handle_generate_brief(tool_inputs)
                        final_result_type = "brief"
                        final_result      = result
                        result_summary    = (
                            f"Brief generated. Found {result.get('raw_trial_count', 0)} active trials "
                            f"and {result.get('sec_filings_found', 0)} SEC filings."
                        )

                    else:
                        result = {"error": f"Unknown tool: {tool_name}"}
                        result_summary = f"Unknown tool: {tool_name}"

                except Exception as exc:
                    logger.error("[Orchestrator] Tool %s failed: %s", tool_name, exc)
                    result = {"error": str(exc)}
                    result_summary = f"Tool failed: {exc}"

                yield {
                    "type":        "tool_done",
                    "tool":        tool_name,
                    "result_type": final_result_type,
                    "result":      final_result,
                }

                # Feed result back to Claude as a compact summary (not the full
                # JSON blob — that would blow the context window)
                tool_results.append({
                    "type":        "tool_result",
                    "tool_use_id": block.id,
                    "content":     result_summary,
                })

            messages.append({"role": "user", "content": tool_results})

    yield {
        "type":        "done",
        "text":        final_text,
        "result_type": final_result_type,
        "result":      final_result,
    }
