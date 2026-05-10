"""
stream_context.py — shared ContextVar for piping token events out of
LangGraph nodes without polluting ARIAState.

Usage:
  # In the orchestrator, before launching the graph:
  from .stream_context import stream_queue_var
  token = stream_queue_var.set(queue)
  try:
      ...run graph...
  finally:
      stream_queue_var.reset(token)

  # Inside any agent node that wants to stream:
  from .stream_context import get_stream_queue
  q = get_stream_queue()
  if q:
      await q.put({"type": "email_chunk", "text": text_chunk})

Python analogy: like Django's thread-local request object — each async
task gets its own value, so two concurrent research runs never cross-wire.
"""
from __future__ import annotations

import asyncio
from contextvars import ContextVar
from typing import Optional

# Each asyncio Task inherits a copy of the context, so concurrent runs
# get independent queues automatically.
stream_queue_var: ContextVar[Optional[asyncio.Queue]] = ContextVar(
    "stream_queue", default=None
)


def get_stream_queue() -> Optional[asyncio.Queue]:
    """Return the queue for the current task, or None if not set."""
    return stream_queue_var.get()
