from __future__ import annotations

import logging
from typing import Any, Dict, List, Optional

from ..db.database import get_db

logger = logging.getLogger(__name__)

# Anthropic pricing per million tokens (input, output) as of early 2025.
PRICING: Dict[str, Dict[str, float]] = {
    "claude-haiku-4-5-20251001": {"input": 0.80,  "output": 4.00},
    "claude-haiku-4-5":          {"input": 0.80,  "output": 4.00},
    "claude-sonnet-4-6":         {"input": 3.00,  "output": 15.00},
    "claude-opus-4-6":           {"input": 15.00, "output": 75.00},
}


def compute_cost(model: str, input_tokens: int, output_tokens: int) -> float:
    """Return cost in USD for one LLM call."""
    prices = PRICING.get(model, {"input": 3.00, "output": 15.00})
    return (
        (input_tokens  / 1_000_000) * prices["input"] +
        (output_tokens / 1_000_000) * prices["output"]
    )


def log_usage(
    org_id: str,
    user_id: str,
    agent: str,
    model: str,
    input_tokens: int,
    output_tokens: int,
    company_name: Optional[str] = None,
) -> float:
    """Persist one usage event. Returns cost in USD."""
    cost = compute_cost(model, input_tokens, output_tokens)
    try:
        conn = get_db()
        with conn:
            conn.execute(
                """INSERT INTO usage_logs
                   (org_id, user_id, agent, model, input_tokens, output_tokens, cost_usd, company_name)
                   VALUES (?, ?, ?, ?, ?, ?, ?, ?)""",
                (org_id, user_id, agent, model, input_tokens, output_tokens, cost, company_name),
            )
        conn.close()
    except Exception as exc:
        logger.warning("[Metering] Failed to log usage: %s", exc)
    return cost


def log_run_usage(
    total_usage: List[Dict[str, Any]],
    org_id: str,
    user_id: str,
    model: str,
    company_name: Optional[str] = None,
) -> None:
    """
    Bulk-log the total_usage list produced by the ARIA agent graph.
    Each entry has keys: agent, input_tokens, output_tokens.
    """
    for entry in total_usage:
        log_usage(
            org_id=org_id,
            user_id=user_id,
            agent=entry.get("agent", "unknown"),
            model=model,
            input_tokens=entry.get("input_tokens", 0),
            output_tokens=entry.get("output_tokens", 0),
            company_name=company_name,
        )


def get_usage_summary(org_id: str) -> Dict[str, Any]:
    """Aggregate usage stats for one org."""
    conn = get_db()

    totals = conn.execute(
        """SELECT COALESCE(SUM(cost_usd), 0) as total_cost,
                  COALESCE(SUM(input_tokens), 0) as total_input,
                  COALESCE(SUM(output_tokens), 0) as total_output,
                  COUNT(*) as total_calls
           FROM usage_logs WHERE org_id = ?""",
        (org_id,),
    ).fetchone()

    by_agent = conn.execute(
        """SELECT agent,
                  ROUND(SUM(cost_usd), 6) as cost,
                  SUM(input_tokens)  as input_tok,
                  SUM(output_tokens) as output_tok,
                  COUNT(*) as calls
           FROM usage_logs WHERE org_id = ?
           GROUP BY agent ORDER BY cost DESC""",
        (org_id,),
    ).fetchall()

    by_day = conn.execute(
        """SELECT DATE(created_at) as day,
                  ROUND(SUM(cost_usd), 6) as cost,
                  COUNT(*) as calls
           FROM usage_logs WHERE org_id = ?
           GROUP BY day ORDER BY day""",
        (org_id,),
    ).fetchall()

    conn.close()

    return {
        "org_id": org_id,
        "totals": dict(totals) if totals else {},
        "by_agent": [dict(r) for r in by_agent],
        "by_day":   [dict(r) for r in by_day],
    }


def get_all_orgs_summary() -> List[Dict[str, Any]]:
    """Usage totals across all orgs (for admin overview)."""
    conn = get_db()
    rows = conn.execute(
        """SELECT o.id, o.name, o.plan,
                  ROUND(COALESCE(SUM(u.cost_usd), 0), 6) as total_cost,
                  COALESCE(COUNT(u.id), 0) as total_calls
           FROM orgs o LEFT JOIN usage_logs u ON o.id = u.org_id
           GROUP BY o.id ORDER BY total_cost DESC"""
    ).fetchall()
    conn.close()
    return [dict(r) for r in rows]
