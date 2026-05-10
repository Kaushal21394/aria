from __future__ import annotations

from typing import Any, Dict, List, Optional

from pydantic import BaseModel


class TrialRecord(BaseModel):
    nct_id: str
    title: str
    phase: Optional[str]
    status: str
    condition: Optional[str]
    start_date: Optional[str]
    lead_sponsor: str


class TrialActivity(BaseModel):
    total_active_trials: int
    phases: Dict[str, int]           # e.g. {"PHASE1": 3, "PHASE2": 8}
    therapeutic_areas: List[str]
    geographic_spread: List[str]


class SponsorBrief(BaseModel):
    company_name: str
    company_overview: str
    pipeline_summary: List[Dict[str, Any]]
    trial_activity: TrialActivity
    opportunity_signals: List[str]
    recommended_service_areas: List[str]


class UsageLog(BaseModel):
    model: str
    input_tokens: int
    output_tokens: int


class BriefConfig(BaseModel):
    """Optional filters passed by the caller to narrow the brief's focus."""
    therapeutic_area: Optional[str] = None   # e.g. "Oncology", "Rare Disease"
    phase: Optional[str] = None              # e.g. "PHASE2", "PHASE3"


class BriefResponse(BaseModel):
    brief: SponsorBrief
    raw_trial_count: int
    sec_filings_found: int
    usage: UsageLog
    config: Optional[BriefConfig] = None
    status: str = "success"


# ---------------------------------------------------------------------------
# Phase 2 — Multi-Agent Research Workflow
# ---------------------------------------------------------------------------

class ResearchFilters(BaseModel):
    """Optional filters forwarded from the UI to focus the research pipeline."""
    therapeutic_area: Optional[str] = None   # e.g. "oncology", "neurology"
    phase: Optional[str] = None              # e.g. "Phase II", "Phase III"
    geography: Optional[str] = None          # e.g. "north_america", "europe"


class ResearchRequest(BaseModel):
    company_name: str
    goal: str = ""                           # Natural language goal — drives planner routing
    filters: ResearchFilters = ResearchFilters()   # Optional; kept for backwards compat
    previous_context: Optional[Dict[str, Any]] = None  # trial_data, intel_data, fit_score from prior run — skip re-fetching


class ResearchResult(BaseModel):
    company_name: str
    goal: str = ""
    execution_plan: Dict[str, Any] = {}     # Planner's routing decision (for auditability)
    trial_data: Dict[str, Any]
    intel_data: Dict[str, Any]
    fit_score: Dict[str, Any]
    rag_context: List[Dict[str, Any]] = []
    synthesis: str                           # Freeform output (email, brief, summary, snapshot)
    mcp_actions: List[Dict[str, Any]] = []
    errors: List[str]
    total_usage: List[Dict[str, Any]]


class ResearchResponse(BaseModel):
    result: ResearchResult
    status: str = "success"
