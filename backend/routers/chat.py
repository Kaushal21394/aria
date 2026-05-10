from __future__ import annotations

import json
import logging
import uuid
from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import StreamingResponse
from pydantic import BaseModel

from ..auth.tokens import get_current_user
from ..db.database import get_db
from ..middleware.rate_limit import check_rate_limit
from ..services.chat_orchestrator import orchestrate

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/chat", tags=["chat"])


# ── Pydantic models ────────────────────────────────────────────────────────

class SessionOut(BaseModel):
    id: str
    title: str
    created_at: str
    updated_at: str


class MessageOut(BaseModel):
    id: int
    role: str
    content: str
    result_type: Optional[str] = None
    result_data: Optional[dict] = None
    created_at: str


class SendMessageBody(BaseModel):
    content: str


# ── Session CRUD ───────────────────────────────────────────────────────────

@router.post("/sessions", response_model=SessionOut)
def create_session(current_user: dict = Depends(get_current_user)) -> SessionOut:
    """Create a new chat session for the authenticated user."""
    session_id = str(uuid.uuid4())
    conn = get_db()
    with conn:
        conn.execute(
            "INSERT INTO chat_sessions (id, org_id, user_id) VALUES (?, ?, ?)",
            (session_id, current_user["org_id"], current_user["user_id"]),
        )
    row = conn.execute(
        "SELECT id, title, created_at, updated_at FROM chat_sessions WHERE id = ?",
        (session_id,),
    ).fetchone()
    conn.close()
    return SessionOut(**dict(row))


@router.get("/sessions", response_model=List[SessionOut])
def list_sessions(current_user: dict = Depends(get_current_user)) -> List[SessionOut]:
    """List all sessions for the authenticated user, newest first."""
    conn = get_db()
    rows = conn.execute(
        """SELECT id, title, created_at, updated_at
           FROM chat_sessions
           WHERE org_id = ? AND user_id = ?
           ORDER BY updated_at DESC""",
        (current_user["org_id"], current_user["user_id"]),
    ).fetchall()
    conn.close()
    return [SessionOut(**dict(r)) for r in rows]


@router.delete("/sessions/{session_id}", status_code=204)
def delete_session(
    session_id: str,
    current_user: dict = Depends(get_current_user),
) -> None:
    conn = get_db()
    conn.execute(
        "DELETE FROM chat_sessions WHERE id = ? AND org_id = ? AND user_id = ?",
        (session_id, current_user["org_id"], current_user["user_id"]),
    )
    conn.commit()
    conn.close()


@router.get("/sessions/{session_id}/history", response_model=List[MessageOut])
def get_history(
    session_id: str,
    current_user: dict = Depends(get_current_user),
) -> List[MessageOut]:
    """Return all messages in a session."""
    conn = get_db()
    # Verify ownership
    session = conn.execute(
        "SELECT id FROM chat_sessions WHERE id = ? AND org_id = ? AND user_id = ?",
        (session_id, current_user["org_id"], current_user["user_id"]),
    ).fetchone()
    if session is None:
        conn.close()
        raise HTTPException(status_code=404, detail="Session not found")

    rows = conn.execute(
        """SELECT id, role, content, result_type, result_data, created_at
           FROM chat_messages WHERE session_id = ? ORDER BY id""",
        (session_id,),
    ).fetchall()
    conn.close()

    out = []
    for r in rows:
        d = dict(r)
        if d.get("result_data"):
            try:
                d["result_data"] = json.loads(d["result_data"])
            except Exception:
                d["result_data"] = None
        out.append(MessageOut(**d))
    return out


# ── SSE message endpoint ───────────────────────────────────────────────────

@router.post("/sessions/{session_id}/message")
async def send_message(
    session_id: str,
    body: SendMessageBody,
    current_user: dict = Depends(check_rate_limit),
) -> StreamingResponse:
    """
    Send a user message and receive the assistant reply as an SSE stream.

    SSE event shapes:
      {"type": "thinking"}
      {"type": "tool_start",  "tool": str, "input": {}}
      {"type": "agent_step",  "agent": str, "message": str}
      {"type": "tool_done",   "tool": str, "result_type": str, "result": {}}
      {"type": "text_chunk",  "text": str}
      {"type": "done",        "text": str, "result_type": str|null, "result": {}|null}
      {"type": "error",       "message": str}
    """
    content = body.content.strip()
    if not content:
        raise HTTPException(status_code=422, detail="Message content cannot be empty")

    conn = get_db()
    session = conn.execute(
        "SELECT id FROM chat_sessions WHERE id = ? AND org_id = ? AND user_id = ?",
        (session_id, current_user["org_id"], current_user["user_id"]),
    ).fetchone()
    conn.close()

    if session is None:
        raise HTTPException(status_code=404, detail="Session not found")

    async def event_generator():
        def _sse(payload: dict) -> str:
            return f"data: {json.dumps(payload)}\n\n"

        # ── Persist user message ───────────────────────────────────────────
        conn = get_db()
        with conn:
            conn.execute(
                "INSERT INTO chat_messages (session_id, role, content) VALUES (?, 'user', ?)",
                (session_id, content),
            )
            # Update session title from first user message if still default
            session_row = conn.execute(
                "SELECT title FROM chat_sessions WHERE id = ?", (session_id,)
            ).fetchone()
            if session_row and session_row["title"] == "New conversation":
                title = content[:60] + ("…" if len(content) > 60 else "")
                conn.execute(
                    "UPDATE chat_sessions SET title = ?, updated_at = datetime('now') WHERE id = ?",
                    (title, session_id),
                )

        # ── Load history (all prior turns for context) ─────────────────────
        history_rows = conn.execute(
            """SELECT role, content FROM chat_messages
               WHERE session_id = ? AND id < (SELECT MAX(id) FROM chat_messages WHERE session_id = ?)
               ORDER BY id""",
            (session_id, session_id),
        ).fetchall()
        conn.close()

        # Build history: for assistant turns, use the commentary text.
        # Tool results are summarised inside the orchestrator — we don't
        # replay the full JSON blobs into the LLM context window.
        history = [{"role": r["role"], "content": r["content"]} for r in history_rows]

        # ── Stream orchestrator events ─────────────────────────────────────
        final_text        = ""
        final_result_type = None
        final_result      = None

        try:
            async for event in orchestrate(
                user_message=content,
                history=history,
                org_id=current_user["org_id"],
                user_id=current_user["user_id"],
            ):
                if event["type"] == "done":
                    final_text        = event.get("text", "")
                    final_result_type = event.get("result_type")
                    final_result      = event.get("result")
                yield _sse(event)

        except Exception as exc:
            logger.error("[Chat] Orchestrator error session=%s: %s", session_id, exc)
            yield _sse({"type": "error", "message": str(exc)})
            return

        # ── Persist assistant message ──────────────────────────────────────
        conn = get_db()
        with conn:
            conn.execute(
                """INSERT INTO chat_messages
                   (session_id, role, content, result_type, result_data)
                   VALUES (?, 'assistant', ?, ?, ?)""",
                (
                    session_id,
                    final_text,
                    final_result_type,
                    json.dumps(final_result) if final_result else None,
                ),
            )
            conn.execute(
                "UPDATE chat_sessions SET updated_at = datetime('now') WHERE id = ?",
                (session_id,),
            )
        conn.close()

    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream",
        headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no"},
    )
