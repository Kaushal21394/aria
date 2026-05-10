from __future__ import annotations

import json
import logging

from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import StreamingResponse

from ..agents.graph import build_aria_graph
from ..config import settings
from ..middleware.rate_limit import check_rate_limit
from ..models.schemas import ResearchFilters, ResearchRequest, ResearchResponse, ResearchResult
from ..services.metering import log_run_usage

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/research", tags=["research"])


def _empty_state(filters: ResearchFilters | None = None, previous_context: dict | None = None) -> dict:
    # NOTE: user_goal, org_id, user_id are intentionally excluded here —
    # they are set explicitly in the initial_state dict and must not be
    # overwritten by this spread.
    state = {
        "execution_plan": {},
        "search_filters": {
            k: v for k, v in (filters.model_dump() if filters else {}).items() if v
        },
        "trial_data":     {},
        "intel_data":     {},
        "fit_score":      {},
        "rag_context":    [],
        "synthesis":      "",
        "mcp_actions":    [],
        "errors":         [],
        "total_usage":    [],
    }
    # Pre-seed data fields from a prior run — agents will self-skip when they
    # find their field already populated, avoiding redundant fetches/LLM calls.
    if previous_context:
        for key in ("trial_data", "intel_data", "fit_score", "rag_context"):
            if previous_context.get(key):
                state[key] = previous_context[key]
    return state


@router.post("/run", response_model=ResearchResponse)
async def run_research(
    request: ResearchRequest,
    current_user: dict = Depends(check_rate_limit),
) -> ResearchResponse:
    """
    Run the full 4-agent ARIA research workflow synchronously.

    Requires: Bearer <JWT> or Bearer sk_* API key header.
    """
    company_name = request.company_name.strip()
    if len(company_name) < 2:
        raise HTTPException(status_code=400, detail="company_name must be at least 2 characters")

    logger.info("[Research] Starting for %s  org=%s user=%s", company_name,
                current_user["org_id"], current_user["user_id"])

    goal = request.goal.strip()

    graph = build_aria_graph()
    initial_state = {
        "company_name": company_name,
        "user_goal":    goal,
        "org_id":       current_user["org_id"],
        "user_id":      current_user["user_id"],
        **_empty_state(request.filters, request.previous_context),
    }

    try:
        result = await graph.ainvoke(initial_state)
    except Exception as exc:
        logger.error("[Research] Graph failed for %s: %s", company_name, exc)
        raise HTTPException(status_code=500, detail=f"Research workflow failed: {exc}")

    # Persist usage to SQLite
    log_run_usage(
        total_usage=result.get("total_usage", []),
        org_id=current_user["org_id"],
        user_id=current_user["user_id"],
        model=settings.aria_model,
        company_name=company_name,
    )

    return ResearchResponse(
        result=ResearchResult(
            company_name=company_name,
            goal=goal,
            execution_plan=result.get("execution_plan", {}),
            trial_data=result.get("trial_data", {}),
            intel_data=result.get("intel_data", {}),
            fit_score=result.get("fit_score", {}),
            rag_context=result.get("rag_context", []),
            synthesis=result.get("synthesis", ""),
            mcp_actions=result.get("mcp_actions", []),
            errors=result.get("errors", []),
            total_usage=result.get("total_usage", []),
        )
    )


@router.post("/stream/{company_name}")
async def stream_research(
    company_name: str,
    request: ResearchRequest = ResearchRequest(company_name=""),
    current_user: dict = Depends(check_rate_limit),
) -> StreamingResponse:
    """
    SSE streaming version of the research workflow.

    Event types:
      {"type": "status",         "message": "..."}
      {"type": "agent_complete", "agent": "...", "message": "...", "data": {...}}
      {"type": "done",           "result": {...}}
      {"type": "error",          "message": "..."}
    """
    company_name = company_name.strip()
    if len(company_name) < 2:
        raise HTTPException(status_code=400, detail="company_name must be at least 2 characters")

    async def event_generator():
        def _sse(payload: dict) -> str:
            return f"data: {json.dumps(payload)}\n\n"

        AGENT_MESSAGES = {
            "planner":     "Analysing your goal and planning the research workflow…",
            "trial_agent": "Fetching clinical trial data from ClinicalTrials.gov…",
            "intel_agent": "Gathering market intelligence signals…",
            "fit_scorer":  "Scoring sponsor fit across 5 dimensions…",
            "synthesizer": "Synthesising results into your requested output…",
        }

        goal = request.goal.strip()
        filters = request.filters
        yield _sse({"type": "status", "message": f"Starting ARIA research for {company_name}…"})

        graph = build_aria_graph()
        base = _empty_state(filters, request.previous_context)
        initial_state = {
            "company_name": company_name,
            "user_goal":    goal,
            "org_id":       current_user["org_id"],
            "user_id":      current_user["user_id"],
            **base,
        }

        accumulated: dict = {
            "company_name": company_name,
            **base,
            "errors":      [],
            "total_usage": [],
        }

        try:
            async for chunk in graph.astream(initial_state, stream_mode="updates"):
                for node_name, updates in chunk.items():
                    if not updates:
                        continue
                    for key, value in updates.items():
                        if key in ("errors", "total_usage"):
                            accumulated[key] = accumulated.get(key, []) + (value or [])
                        else:
                            accumulated[key] = value

                    yield _sse({
                        "type":    "agent_complete",
                        "agent":   node_name,
                        "message": AGENT_MESSAGES.get(node_name, f"{node_name} complete"),
                        "data": {
                            k: v for k, v in updates.items()
                            if k not in ("errors", "total_usage")
                        },
                    })

        except Exception as exc:
            logger.error("[Research Stream] Error for %s: %s", company_name, exc)
            yield _sse({"type": "error", "message": str(exc)})
            return

        # Persist usage after stream completes
        log_run_usage(
            total_usage=accumulated.get("total_usage", []),
            org_id=current_user["org_id"],
            user_id=current_user["user_id"],
            model=settings.aria_model,
            company_name=company_name,
        )

        yield _sse({
            "type": "done",
            "result": {
                "company_name":   company_name,
                "goal":           goal,
                "execution_plan": accumulated.get("execution_plan", {}),
                "trial_data":     accumulated.get("trial_data", {}),
                "intel_data":     accumulated.get("intel_data", {}),
                "fit_score":      accumulated.get("fit_score", {}),
                "rag_context":    accumulated.get("rag_context", []),
                "synthesis":      accumulated.get("synthesis", ""),
                "mcp_actions":    accumulated.get("mcp_actions", []),
                "errors":         accumulated.get("errors", []),
                "total_usage":    accumulated.get("total_usage", []),
            },
        })

    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream",
        headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no"},
    )
