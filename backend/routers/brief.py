from __future__ import annotations

import asyncio
import json
import logging

from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import StreamingResponse

from ..config import settings
from ..middleware.rate_limit import check_rate_limit
from ..models.schemas import BriefConfig, BriefResponse
from ..services.brief_generator import generate_brief, stream_brief_events
from ..services.clinical_trials import fetch_trials
from ..services.metering import log_usage
from ..services.sec_edgar import fetch_sec_filings

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/brief", tags=["brief"])


@router.post("/{company_name}", response_model=BriefResponse)
async def generate_sponsor_brief(
    company_name: str,
    config: BriefConfig = BriefConfig(),
    current_user: dict = Depends(check_rate_limit),
) -> BriefResponse:
    """
    Given a pharma/biotech company name, fetch public data and return
    a structured BD intelligence brief.

    Requires: Bearer <JWT> or Bearer sk_* API key header.
    """
    if not company_name or len(company_name.strip()) < 2:
        raise HTTPException(status_code=400, detail="company_name must be at least 2 characters")

    company_name = company_name.strip()
    logger.info("Brief for: %s  org=%s user=%s", company_name,
                current_user["org_id"], current_user["user_id"])

    config_dict = config.model_dump(exclude_none=True) or None

    try:
        trials, sec_data = await asyncio.gather(
            fetch_trials(company_name, therapeutic_area=config.therapeutic_area, phase=config.phase),
            fetch_sec_filings(company_name),
        )
    except Exception as exc:
        logger.error("Data fetch failed for %s: %s", company_name, exc)
        raise HTTPException(status_code=502, detail=f"External data fetch failed: {str(exc)}")

    logger.info("Fetched %d trials, %d SEC filings for %s",
                len(trials), sec_data.get("total_filings_found", 0), company_name)

    try:
        brief, usage = generate_brief(company_name, trials, sec_data, config_dict)
    except json.JSONDecodeError as exc:
        logger.error("JSON parse failed for %s: %s", company_name, exc)
        raise HTTPException(status_code=500, detail="Failed to parse model response as JSON")
    except Exception as exc:
        logger.error("Brief generation failed for %s: %s", company_name, exc)
        raise HTTPException(status_code=500, detail=f"Brief generation failed: {str(exc)}")

    # Persist usage
    log_usage(
        org_id=current_user["org_id"],
        user_id=current_user["user_id"],
        agent="brief_generator",
        model=settings.aria_model,
        input_tokens=usage.input_tokens,
        output_tokens=usage.output_tokens,
        company_name=company_name,
    )

    return BriefResponse(
        brief=brief,
        raw_trial_count=len(trials),
        sec_filings_found=sec_data.get("total_filings_found", 0),
        usage=usage,
        config=config if config_dict else None,
    )


@router.post("/stream/{company_name}")
async def stream_sponsor_brief(
    company_name: str,
    config: BriefConfig = BriefConfig(),
    current_user: dict = Depends(check_rate_limit),
) -> StreamingResponse:
    """
    Streaming version of the brief endpoint using Server-Sent Events.
    Requires: Bearer <JWT> or Bearer sk_* API key header.
    """
    if not company_name or len(company_name.strip()) < 2:
        raise HTTPException(status_code=400, detail="company_name must be at least 2 characters")

    company_name = company_name.strip()
    logger.info("Streaming brief for: %s  org=%s", company_name, current_user["org_id"])
    config_dict = config.model_dump(exclude_none=True) or None

    async def event_generator():
        def sse(payload: dict) -> str:
            return f"data: {json.dumps(payload)}\n\n"

        filter_note = ""
        if config_dict:
            parts = [f"{k}={v}" for k, v in config_dict.items()]
            filter_note = f" [{', '.join(parts)}]"

        yield sse({"type": "status", "message": f"Fetching trials from ClinicalTrials.gov and SEC EDGAR{filter_note}…"})

        try:
            trials, sec_data = await asyncio.gather(
                fetch_trials(company_name, therapeutic_area=config.therapeutic_area, phase=config.phase),
                fetch_sec_filings(company_name),
            )
        except Exception as exc:
            yield sse({"type": "error", "message": f"Data fetch failed: {exc}"})
            return

        yield sse({
            "type": "status",
            "message": f"Found {len(trials)} active trials. Generating brief with Claude…",
        })

        # Stream events and capture usage from the done event
        usage_captured = {}

        async def _patched():
            async for event in stream_brief_events(company_name, trials, sec_data, config_dict):
                if '"type": "done"' in event or '"type":"done"' in event:
                    try:
                        data = json.loads(event.removeprefix("data: ").strip())
                        if data.get("usage"):
                            usage_captured.update(data["usage"])
                    except Exception:
                        pass
                yield event

        async for chunk in _patched():
            yield chunk

        # Persist usage (best-effort — usage may not be captured for all stream paths)
        if usage_captured:
            log_usage(
                org_id=current_user["org_id"],
                user_id=current_user["user_id"],
                agent="brief_generator",
                model=settings.aria_model,
                input_tokens=usage_captured.get("input_tokens", 0),
                output_tokens=usage_captured.get("output_tokens", 0),
                company_name=company_name,
            )

    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream",
        headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no"},
    )
