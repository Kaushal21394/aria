from __future__ import annotations

from typing import Any, Dict, List

import httpx

# EDGAR full-text search — returns filing metadata for a company
EDGAR_FTS_URL = "https://efts.sec.gov/LATEST/search-index"

# EDGAR requires a User-Agent header identifying the caller
EDGAR_HEADERS = {
    "User-Agent": "ARIA Research Tool aria-research@example.com",
    "Accept": "application/json",
}


async def fetch_sec_filings(company_name: str) -> Dict[str, Any]:
    """
    Search SEC EDGAR for recent 10-K/10-Q filings by the company.
    Returns filing metadata (dates, form types) as a signal of SEC presence.
    """
    params = {
        "q": f'"{company_name}"',
        "dateRange": "custom",
        "startdt": "2023-01-01",
        "forms": "10-K,10-Q",
    }

    async with httpx.AsyncClient(timeout=30.0) as client:
        response = await client.get(EDGAR_FTS_URL, params=params, headers=EDGAR_HEADERS)
        response.raise_for_status()
        data = response.json()

    hits: List[Dict[str, Any]] = data.get("hits", {}).get("hits", [])
    total: int = data.get("hits", {}).get("total", {}).get("value", 0)

    filings = []
    for hit in hits[:5]:
        src = hit.get("_source", {})
        filings.append(
            {
                "form_type": src.get("form_type", ""),
                "file_date": src.get("file_date", ""),
                "entity_name": src.get("entity_name", ""),
                "period_of_report": src.get("period_of_report", ""),
            }
        )

    return {
        "total_filings_found": total,
        "recent_filings": filings,
        "is_public_company": total > 0,
    }
