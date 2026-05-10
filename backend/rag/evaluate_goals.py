"""
ARIA Goal-Fulfillment Evaluator
================================
Replaces the RAGAS harness (which requires fixed Q&A pairs) with an
LLM-as-judge approach that measures how well the pipeline's freeform
output fulfils the user's original goal.

Run:
    python -m backend.rag.evaluate_goals

Outputs a table of scores and a summary pass/fail per golden goal.
Target: mean score >= 3.5 / 5.0
"""
from __future__ import annotations

import asyncio
import json
import logging
import sys
from dataclasses import dataclass, field
from typing import Any, Dict, List

import anthropic

from ..agents.graph import build_aria_graph
from ..config import settings

logging.basicConfig(level=logging.WARNING)
logger = logging.getLogger(__name__)

# ── Golden goals — 10 fixed goals covering all 4 output formats ──────────────
# These serve as regression tests: if routing or output quality degrades,
# scores drop and you know something changed.

GOLDEN_GOALS = [
    # outreach_email (3)
    {
        "company": "Pfizer",
        "goal": "Draft a personalised BD outreach email to Pfizer's oncology clinical operations team",
        "expected_format": "outreach_email",
        "expected_agents": ["trial", "intel", "fit"],
    },
    {
        "company": "Moderna",
        "goal": "Write a cold outreach email to Moderna about partnering on their mRNA vaccine trials",
        "expected_format": "outreach_email",
        "expected_agents": ["trial", "intel", "fit"],
    },
    {
        "company": "AstraZeneca",
        "goal": "Compose an outreach email to AstraZeneca's R&D BD team positioning our Phase III oncology capabilities",
        "expected_format": "outreach_email",
        "expected_agents": ["trial", "intel", "fit"],
    },
    # competitive_brief (2)
    {
        "company": "Roche",
        "goal": "Give me a competitive landscape brief on Roche — where are the CRO opportunities?",
        "expected_format": "competitive_brief",
        "expected_agents": ["trial", "intel", "fit"],
    },
    {
        "company": "Novartis",
        "goal": "Produce a competitive BD brief for Novartis covering their pipeline and partnership potential",
        "expected_format": "competitive_brief",
        "expected_agents": ["trial", "intel", "fit"],
    },
    # pipeline_summary (2)
    {
        "company": "Bristol Myers Squibb",
        "goal": "Summarise Bristol Myers Squibb's active pipeline and flag any CRO outsourcing opportunities",
        "expected_format": "pipeline_summary",
        "expected_agents": ["trial", "intel"],
    },
    {
        "company": "Eli Lilly",
        "goal": "Give me a pipeline summary for Eli Lilly — what are they working on and where might they need CRO support?",
        "expected_format": "pipeline_summary",
        "expected_agents": ["trial", "intel"],
    },
    # account_snapshot (3)
    {
        "company": "Regeneron",
        "goal": "Quick snapshot on Regeneron — who are they and why should I care about them as a BD target?",
        "expected_format": "account_snapshot",
        "expected_agents": ["trial", "intel"],
    },
    {
        "company": "Vertex Pharmaceuticals",
        "goal": "Give me a quick exec summary on Vertex Pharmaceuticals",
        "expected_format": "account_snapshot",
        "expected_agents": ["trial", "intel"],
    },
    {
        "company": "Biogen",
        "goal": "What's the short story on Biogen — pipeline, focus, and BD relevance?",
        "expected_format": "account_snapshot",
        "expected_agents": ["trial", "intel"],
    },
]

# ── Judge prompt ──────────────────────────────────────────────────────────────

JUDGE_SYSTEM = """You are an expert evaluator assessing AI-generated research outputs for a pharma BD intelligence platform.

Score the output on three dimensions (1–5 each):
- relevance:    Does the output directly address the user's stated goal?
- completeness: Does it cover the key information needed to act on the goal?
- quality:      Is it well-written, specific, and useful (not generic or vague)?

Return ONLY valid JSON:
{
  "relevance": 1-5,
  "completeness": 1-5,
  "quality": 1-5,
  "mean": <float average of the three>,
  "verdict": "pass" or "fail",
  "notes": "one sentence explaining the score"
}

"pass" if mean >= 3.5, "fail" otherwise."""


@dataclass
class EvalResult:
    company: str
    goal: str
    expected_format: str
    actual_format: str
    format_match: bool
    agents_used: List[str]
    relevance: float = 0.0
    completeness: float = 0.0
    quality: float = 0.0
    mean: float = 0.0
    verdict: str = "fail"
    notes: str = ""
    error: str = ""


def _strip_fences(text: str) -> str:
    text = text.strip()
    if text.startswith("```"):
        lines = [ln for ln in text.splitlines() if not ln.strip().startswith("```")]
        text = "\n".join(lines).strip()
    return text


async def _judge(client: anthropic.AsyncAnthropic, goal: str, synthesis: str) -> Dict[str, Any]:
    prompt = f"User goal: {goal}\n\nGenerated output:\n{synthesis}\n\nScore this output."
    response = await client.messages.create(
        model=settings.aria_model,
        max_tokens=256,
        system=JUDGE_SYSTEM,
        messages=[{"role": "user", "content": prompt}],
    )
    text = " ".join(b.text for b in response.content if hasattr(b, "type") and b.type == "text")
    return json.loads(_strip_fences(text))


async def _run_one(golden: dict, graph, client: anthropic.AsyncAnthropic) -> EvalResult:
    result = EvalResult(
        company=golden["company"],
        goal=golden["goal"],
        expected_format=golden["expected_format"],
        actual_format="",
        format_match=False,
        agents_used=[],
    )

    try:
        state = await graph.ainvoke({
            "company_name":   golden["company"],
            "user_goal":      golden["goal"],
            "user_id":        "eval",
            "org_id":         "eval",
            "execution_plan": {},
            "search_filters": {},
            "trial_data":     {},
            "intel_data":     {},
            "fit_score":      {},
            "rag_context":    [],
            "synthesis":      "",
            "mcp_actions":    [],
            "errors":         [],
            "total_usage":    [],
        })

        plan = state.get("execution_plan", {})
        result.actual_format = plan.get("output_format", "unknown")
        result.agents_used = plan.get("agents", [])
        result.format_match = result.actual_format == result.expected_format
        synthesis = state.get("synthesis", "")

        if not synthesis:
            result.error = "Empty synthesis output"
            return result

        scores = await _judge(client, golden["goal"], synthesis)
        result.relevance    = scores.get("relevance", 0)
        result.completeness = scores.get("completeness", 0)
        result.quality      = scores.get("quality", 0)
        result.mean         = scores.get("mean", 0)
        result.verdict      = scores.get("verdict", "fail")
        result.notes        = scores.get("notes", "")

    except Exception as exc:
        result.error = str(exc)

    return result


def _print_table(results: List[EvalResult]) -> None:
    print("\n" + "=" * 90)
    print(f"{'Company':<25} {'Format':>18} {'Match':>6} {'Rel':>5} {'Comp':>6} {'Qual':>6} {'Mean':>6} {'Pass?':>6}")
    print("-" * 90)

    passes = 0
    for r in results:
        if r.error:
            print(f"{r.company:<25} {'ERROR':>18}   {'':>5} {'':>5} {'':>6} {'':>6} {'':>6} {'':>6}")
            print(f"  ↳ {r.error}")
            continue
        match_str = "✓" if r.format_match else "✗"
        verdict_str = "PASS" if r.verdict == "pass" else "FAIL"
        if r.verdict == "pass":
            passes += 1
        print(
            f"{r.company:<25} {r.actual_format:>18} {match_str:>6} "
            f"{r.relevance:>5.1f} {r.completeness:>6.1f} {r.quality:>6.1f} "
            f"{r.mean:>6.2f} {verdict_str:>6}"
        )
        if r.notes:
            print(f"  ↳ {r.notes}")

    valid = [r for r in results if not r.error]
    if valid:
        mean_score = sum(r.mean for r in valid) / len(valid)
        fmt_match_pct = sum(1 for r in valid if r.format_match) / len(valid) * 100
        print("=" * 90)
        print(f"Results: {passes}/{len(valid)} passed  |  Mean score: {mean_score:.2f}/5.0  |  Format accuracy: {fmt_match_pct:.0f}%")
        target = mean_score >= 3.5
        print(f"Target (mean ≥ 3.5): {'PASS ✓' if target else 'FAIL ✗'}")


async def main() -> None:
    print("ARIA Goal-Fulfillment Evaluation")
    print(f"Model: {settings.aria_model}  |  Goals: {len(GOLDEN_GOALS)}")
    print("Building graph…")

    graph = build_aria_graph()
    client = anthropic.AsyncAnthropic(api_key=settings.anthropic_api_key)

    print("Running evaluations (this will take a few minutes)…\n")
    results: List[EvalResult] = []

    for i, golden in enumerate(GOLDEN_GOALS, 1):
        print(f"  [{i}/{len(GOLDEN_GOALS)}] {golden['company']} — {golden['goal'][:60]}…")
        result = await _run_one(golden, graph, client)
        results.append(result)
        # Brief pause between runs to respect rate limits
        if i < len(GOLDEN_GOALS):
            await asyncio.sleep(5)

    _print_table(results)


if __name__ == "__main__":
    asyncio.run(main())
