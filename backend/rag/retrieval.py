"""
RAG retrieval for ARIA Phase 3.

Provides semantic search over the CRO proposals corpus with optional metadata
filtering (therapeutic area, phase, outcome).

The Outreach Drafter agent calls retrieve_proposals() to get evidence-backed
context before writing a sponsor email.
"""
from __future__ import annotations

import logging
from typing import Any, Dict, List, Optional

from openai import OpenAI

from ..config import settings
from .ingest import EMBED_MODEL, get_collection

logger = logging.getLogger(__name__)


def _embed_query(query: str) -> List[float]:
    client = OpenAI(api_key=settings.openai_api_key)
    response = client.embeddings.create(model=EMBED_MODEL, input=[query])
    return response.data[0].embedding


def retrieve_proposals(
    query: str,
    therapeutic_area: Optional[str] = None,
    phase: Optional[str] = None,
    outcome: Optional[str] = None,
    top_k: int = 3,
) -> List[Dict[str, Any]]:
    """
    Retrieve the top-K most relevant proposal chunks for a given query.

    Args:
        query:             Free-text query (e.g. "Phase II oncology US sponsor").
        therapeutic_area:  Filter to a specific TA (e.g. "oncology", "neurology").
                           Must exactly match corpus metadata values.
        phase:             Filter by phase (e.g. "Phase II", "Phase III").
        outcome:           Filter by outcome ("won", "lost", "ongoing").
        top_k:             Number of results to return.

    Returns:
        List of dicts with keys: text, score, proposal_id, therapeutic_area,
        phase, service_type, geography, outcome, year, sponsor_size, chunk_index.
    """
    collection = get_collection()

    # Build ChromaDB $and filter if any metadata filters provided
    filters: Dict[str, Any] = {}
    conditions = []
    if therapeutic_area:
        conditions.append({"therapeutic_area": {"$eq": therapeutic_area}})
    if phase:
        conditions.append({"phase": {"$eq": phase}})
    if outcome:
        conditions.append({"outcome": {"$eq": outcome}})

    if len(conditions) == 1:
        filters = conditions[0]
    elif len(conditions) > 1:
        filters = {"$and": conditions}

    query_vec = _embed_query(query)

    kwargs: Dict[str, Any] = {
        "query_embeddings": [query_vec],
        "n_results": top_k,
        "include": ["documents", "metadatas", "distances"],
    }
    if filters:
        kwargs["where"] = filters

    try:
        results = collection.query(**kwargs)
    except Exception as exc:
        # If filtered query returns fewer results than top_k, ChromaDB raises.
        # Fall back to unfiltered search.
        logger.warning("[RAG] Filtered query failed (%s), falling back to unfiltered.", exc)
        kwargs.pop("where", None)
        results = collection.query(**kwargs)

    hits = []
    for doc, meta, dist in zip(
        results["documents"][0],
        results["metadatas"][0],
        results["distances"][0],
    ):
        hits.append({
            "text":             doc,
            "score":            round(1.0 - dist, 4),   # cosine distance → similarity
            "proposal_id":      meta.get("proposal_id", ""),
            "therapeutic_area": meta.get("therapeutic_area", ""),
            "phase":            meta.get("phase", ""),
            "service_type":     meta.get("service_type", ""),
            "geography":        meta.get("geography", ""),
            "outcome":          meta.get("outcome", ""),
            "year":             meta.get("year", ""),
            "sponsor_size":     meta.get("sponsor_size", ""),
        })

    logger.info(
        "[RAG] Query '%s' (TA=%s, phase=%s) → %d results (top score: %.3f)",
        query[:60], therapeutic_area, phase, len(hits), hits[0]["score"] if hits else 0.0,
    )
    return hits


def format_rag_context(hits: List[Dict[str, Any]]) -> str:
    """
    Format retrieved proposal chunks into a numbered context block
    ready to be injected into an LLM prompt.
    """
    if not hits:
        return "No relevant past proposals found."

    blocks = []
    for i, h in enumerate(hits, 1):
        header = (
            f"[Past Proposal {i}] "
            f"TA: {h['therapeutic_area'].replace('_', ' ').title()} | "
            f"{h['phase']} | "
            f"Outcome: {h['outcome'].upper()} | "
            f"Geography: {h['geography'].replace('_', ' ').title()} | "
            f"Year: {h['year']}"
        )
        blocks.append(f"{header}\n{h['text']}")

    return "\n\n---\n\n".join(blocks)
