"""
RAG ingestion pipeline for ARIA Phase 3.

Builds a persistent ChromaDB vector index from the 50-document CRO proposal corpus.
Uses OpenAI text-embedding-3-small for embeddings (cheap, 1536-dim, production-grade).

Usage:
    # Auto-initializes on first import; call explicitly to force a rebuild:
    from backend.rag.ingest import build_index
    build_index(force_rebuild=True)
"""
from __future__ import annotations

import logging
from typing import List

import chromadb
from openai import OpenAI

from ..config import settings
from .corpus import PROPOSALS

logger = logging.getLogger(__name__)

COLLECTION_NAME = "cro_proposals"
EMBED_MODEL = "text-embedding-3-small"

# Module-level singletons — initialized once per process
_chroma_client: chromadb.PersistentClient | None = None
_collection: chromadb.Collection | None = None


def _get_client() -> chromadb.PersistentClient:
    global _chroma_client
    if _chroma_client is None:
        _chroma_client = chromadb.PersistentClient(path=settings.chroma_path)
    return _chroma_client


def _embed_texts(texts: List[str]) -> List[List[float]]:
    """Call OpenAI text-embedding-3-small on a list of texts."""
    client = OpenAI(api_key=settings.openai_api_key)
    response = client.embeddings.create(model=EMBED_MODEL, input=texts)
    return [item.embedding for item in response.data]


def _chunk_proposal(text: str) -> List[str]:
    """
    Split a proposal into paragraph-level chunks.
    Each proposal is ~200 words, so paragraphs are the natural unit.
    Returns at least one chunk (the full text) if no paragraph breaks found.
    """
    paragraphs = [p.strip() for p in text.split("\n\n") if p.strip()]
    return paragraphs if paragraphs else [text]


def build_index(force_rebuild: bool = False) -> chromadb.Collection:
    """
    Build (or load) the ChromaDB proposals collection.

    Args:
        force_rebuild: If True, deletes and rebuilds the collection even if
                       it already exists.

    Returns:
        The populated ChromaDB collection.
    """
    global _collection
    client = _get_client()

    existing = [c.name for c in client.list_collections()]

    if COLLECTION_NAME in existing:
        if not force_rebuild:
            _collection = client.get_collection(
                name=COLLECTION_NAME,
                embedding_function=None,  # we supply our own embeddings
            )
            count = _collection.count()
            logger.info("[RAG] Loaded existing collection '%s' (%d chunks)", COLLECTION_NAME, count)
            return _collection
        else:
            client.delete_collection(COLLECTION_NAME)
            logger.info("[RAG] Deleted existing collection for rebuild.")

    _collection = client.create_collection(
        name=COLLECTION_NAME,
        metadata={"hnsw:space": "cosine"},
    )
    logger.info("[RAG] Created collection '%s'. Ingesting %d proposals…", COLLECTION_NAME, len(PROPOSALS))

    # Build chunk lists with metadata
    chunk_ids: List[str] = []
    chunk_texts: List[str] = []
    chunk_metadatas: List[dict] = []

    for prop in PROPOSALS:
        chunks = _chunk_proposal(prop["text"])
        for i, chunk in enumerate(chunks):
            chunk_ids.append(f"{prop['id']}_p{i}")
            chunk_texts.append(chunk)
            chunk_metadatas.append({
                "proposal_id":       prop["id"],
                "therapeutic_area":  prop["therapeutic_area"],
                "phase":             prop["phase"],
                "service_type":      prop["service_type"],
                "geography":         prop["geography"],
                "outcome":           prop["outcome"],
                "year":              prop["year"],
                "sponsor_size":      prop["sponsor_size"],
                "chunk_index":       i,
            })

    # Embed in one batch (text-embedding-3-small supports up to 2048 inputs)
    logger.info("[RAG] Embedding %d chunks…", len(chunk_texts))
    embeddings = _embed_texts(chunk_texts)

    # Upsert into ChromaDB
    _collection.add(
        ids=chunk_ids,
        documents=chunk_texts,
        embeddings=embeddings,
        metadatas=chunk_metadatas,
    )

    logger.info("[RAG] Ingestion complete. %d chunks indexed.", len(chunk_ids))
    return _collection


def get_collection() -> chromadb.Collection:
    """
    Return the collection, building the index if it doesn't exist yet.
    Safe to call multiple times — uses module-level singleton.
    """
    global _collection
    if _collection is None:
        _collection = build_index()
    return _collection
