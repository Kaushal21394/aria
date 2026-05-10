from __future__ import annotations

from typing import Any, Dict, List, Optional

import httpx

CTGOV_BASE = "https://clinicaltrials.gov/api/v2/studies"


async def fetch_trials(
    company_name: str,
    max_results: int = 50,
    therapeutic_area: Optional[str] = None,
    phase: Optional[str] = None,
) -> List[Dict[str, Any]]:
    """
    Fetch active/recruiting trials for a sponsor from ClinicalTrials.gov v2 API.
    Docs: https://clinicaltrials.gov/data-api/api

    Optional filters:
      therapeutic_area — freetext condition filter, e.g. "Oncology"
      phase            — e.g. "PHASE2" (matches ClinicalTrials phase enum values)
    """
    params: Dict[str, Any] = {
        "query.spons": company_name,
        "filter.overallStatus": "RECRUITING,ACTIVE_NOT_RECRUITING",
        "fields": "NCTId,BriefTitle,Phase,Condition,LeadSponsorName,StartDate,OverallStatus",
        "pageSize": max_results,
        "format": "json",
    }

    if therapeutic_area:
        params["query.cond"] = therapeutic_area

    if phase:
        # ClinicalTrials v2 phase filter expects values like PHASE1, PHASE2, PHASE3
        params["filter.phase"] = phase.upper().replace(" ", "")

    async with httpx.AsyncClient(timeout=30.0) as client:
        response = await client.get(CTGOV_BASE, params=params)
        response.raise_for_status()
        data = response.json()

    studies = data.get("studies", [])
    results = []

    for study in studies:
        proto = study.get("protocolSection", {})
        id_module = proto.get("identificationModule", {})
        status_module = proto.get("statusModule", {})
        design_module = proto.get("designModule", {})
        conds_module = proto.get("conditionsModule", {})
        sponsor_module = proto.get("sponsorCollaboratorsModule", {})

        phases = design_module.get("phases", [])

        results.append(
            {
                "nct_id": id_module.get("nctId", ""),
                "title": id_module.get("briefTitle", ""),
                "phase": phases[0] if phases else None,
                "status": status_module.get("overallStatus", ""),
                "condition": (conds_module.get("conditions") or [None])[0],
                "start_date": status_module.get("startDateStruct", {}).get("date"),
                "lead_sponsor": sponsor_module.get("leadSponsor", {}).get("name", ""),
            }
        )

    return results
