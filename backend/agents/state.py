from __future__ import annotations

import operator
from typing import Annotated, Any, Dict, List

from typing_extensions import TypedDict


class ARIAState(TypedDict):
    company_name: str
    user_goal: str                           # Natural language goal from the user
    execution_plan: Dict[str, Any]           # Planner's routing decision {agents, output_format, rationale}
    search_filters: Dict[str, str]           # Optional UI-supplied filters (ta, phase, geography)
    trial_data: Dict[str, Any]
    intel_data: Dict[str, Any]
    fit_score: Dict[str, Any]
    rag_context: List[Dict[str, Any]]        # Retrieved proposal chunks (outreach_email only)
    synthesis: str                           # Freeform output from synthesizer
    # Phase 4 — tenant identity (injected by the router before graph.ainvoke)
    org_id: str
    user_id: str
    # Phase 4 — MCP actions executed by the synthesizer (outreach_email only)
    mcp_actions: List[Dict[str, Any]]
    # Reducers: each node appends to these lists rather than replacing them
    errors: Annotated[List[str], operator.add]
    total_usage: Annotated[List[Dict[str, Any]], operator.add]
