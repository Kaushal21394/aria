from __future__ import annotations

from fastapi import APIRouter, Depends

from ..auth.tokens import get_current_user
from ..services.metering import get_all_orgs_summary, get_usage_summary

router = APIRouter(prefix="/admin", tags=["admin"])


@router.get("/usage")
def usage_my_org(current_user: dict = Depends(get_current_user)) -> dict:
    """
    Return cost and token usage summary for the authenticated org.

    Response shape:
    {
      "org_id": str,
      "totals": {"total_cost": float, "total_input": int, "total_output": int, "total_calls": int},
      "by_agent": [{"agent": str, "cost": float, "input_tok": int, "output_tok": int, "calls": int}],
      "by_day":   [{"day": str, "cost": float, "calls": int}]
    }
    """
    return get_usage_summary(current_user["org_id"])


@router.get("/usage/all")
def usage_all_orgs(_: dict = Depends(get_current_user)) -> list:
    """
    Return a cost roll-up across all orgs.
    In production this would be admin-only; here any authenticated user can view it
    for demo/learning purposes.
    """
    return get_all_orgs_summary()
