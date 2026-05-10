/**
 * API client — thin wrapper around fetch.
 * Calls go to /api/... which Vite proxies to FastAPI on :8000.
 *
 * Phase 4: every protected call attaches the JWT stored in module state.
 * Call setAuthToken(token) after login; it persists for the session.
 */

let _authToken = null;

/** Called by App.jsx after successful login. */
export function setAuthToken(token) {
  _authToken = token;
}

function _authHeader() {
  return _authToken ? { Authorization: `Bearer ${_authToken}` } : {};
}

/** Shared SSE stream reader — splits a response body into parsed JSON events. */
async function _readSSE(response, handlers) {
  const reader = response.body.getReader();
  const decoder = new TextDecoder();
  let buffer = "";

  while (true) {
    const { done, value } = await reader.read();
    if (done) break;

    buffer += decoder.decode(value, { stream: true });
    const parts = buffer.split("\n\n");
    buffer = parts.pop();

    for (const part of parts) {
      const line = part.trim();
      if (!line.startsWith("data:")) continue;
      let event;
      try { event = JSON.parse(line.slice(5).trim()); } catch { continue; }
      handlers(event);
    }
  }
}

export async function fetchBrief(companyName) {
  const response = await fetch(
    `/api/brief/${encodeURIComponent(companyName)}`,
    { method: "POST", headers: _authHeader() }
  );

  if (!response.ok) {
    const err = await response.json().catch(() => ({}));
    throw new Error(err.detail || `Request failed (${response.status})`);
  }

  return response.json();
}

/**
 * streamBrief — calls the Phase 1 SSE streaming endpoint.
 *
 * Callbacks:
 *   onStatus(message)  — progress update
 *   onChunk(text)      — raw text fragment from Claude
 *   onDone(data)       — final parsed brief + usage
 *   onError(message)   — something went wrong
 */
export async function streamBrief(companyName, { onStatus, onChunk, onDone, onError }) {
  const response = await fetch(
    `/api/brief/stream/${encodeURIComponent(companyName)}`,
    { method: "POST", headers: _authHeader() }
  );

  if (!response.ok) {
    const err = await response.json().catch(() => ({}));
    onError(err.detail || `Request failed (${response.status})`);
    return;
  }

  await _readSSE(response, (event) => {
    if      (event.type === "status") onStatus(event.message);
    else if (event.type === "chunk")  onChunk(event.text);
    else if (event.type === "done")   onDone(event);
    else if (event.type === "error")  onError(event.message);
  });
}

/**
 * streamResearch — calls the Phase 2/3/4 SSE streaming endpoint.
 *
 * @param {string} companyName
 * @param {object} filters — optional { therapeutic_area, phase, geography }
 * @param {object} callbacks — { onAgentComplete, onDone, onError }
 *
 * Callbacks:
 *   onAgentComplete(agent, data) — fired when each of the 4 agents finishes
 *   onDone(result)               — full ResearchResult incl. mcp_actions
 *   onError(message)             — something went wrong
 */
// ── Chat API ───────────────────────────────────────────────────────────────

export async function createSession() {
  const res = await fetch("/api/chat/sessions", {
    method: "POST",
    headers: _authHeader(),
  });
  if (!res.ok) throw new Error((await res.json().catch(() => ({}))).detail || "Failed to create session");
  return res.json();
}

export async function listSessions() {
  const res = await fetch("/api/chat/sessions", { headers: _authHeader() });
  if (!res.ok) throw new Error("Failed to load sessions");
  return res.json();
}

export async function deleteSession(sessionId) {
  await fetch(`/api/chat/sessions/${sessionId}`, {
    method: "DELETE",
    headers: _authHeader(),
  });
}

export async function getHistory(sessionId) {
  const res = await fetch(`/api/chat/sessions/${sessionId}/history`, {
    headers: _authHeader(),
  });
  if (!res.ok) throw new Error("Failed to load history");
  return res.json();
}

/**
 * streamMessage — send a chat message and receive SSE events.
 *
 * Callbacks:
 *   onThinking()                         — orchestrator decided to call a tool
 *   onToolStart(tool, input)             — tool invocation started
 *   onAgentStep(agent, message)          — live progress inside run_research
 *   onToolDone(tool, resultType, result) — tool finished, result attached
 *   onEmailChunk(text)                   — outreach email token (streams while drafter runs)
 *   onTextChunk(text)                    — streaming assistant commentary token
 *   onDone(text, resultType, result)     — full reply ready
 *   onError(message)
 */
export async function streamMessage(sessionId, content, {
  onThinking, onToolStart, onAgentStep, onToolDone,
  onTextChunk, onDone, onError,
}) {
  const res = await fetch(`/api/chat/sessions/${sessionId}/message`, {
    method: "POST",
    headers: { "Content-Type": "application/json", ..._authHeader() },
    body: JSON.stringify({ content }),
  });

  if (!res.ok) {
    const err = await res.json().catch(() => ({}));
    onError(err.detail || `Request failed (${res.status})`);
    return;
  }

  await _readSSE(res, (event) => {
    if      (event.type === "thinking")    onThinking?.();
    else if (event.type === "tool_start")  onToolStart?.(event.tool, event.input);
    else if (event.type === "agent_step")  onAgentStep?.(event.agent, event.message);
    else if (event.type === "tool_done")   onToolDone?.(event.tool, event.result_type, event.result);
    else if (event.type === "synthesis_chunk") onEmailChunk?.(event.text);
    else if (event.type === "text_chunk")  onTextChunk?.(event.text);
    else if (event.type === "done")        onDone?.(event.text, event.result_type, event.result);
    else if (event.type === "error")       onError?.(event.message);
  });
}

export async function streamResearch(companyName, goal, filters, { onAgentComplete, onDone, onError }, previousContext = null) {
  const body = {
    company_name: companyName,
    goal:         goal || "",
    filters: {
      therapeutic_area: filters?.therapeutic_area || null,
      phase:            filters?.phase            || null,
      geography:        filters?.geography        || null,
    },
    // Carry forward data from the previous run so agents can skip re-fetching
    previous_context: previousContext
      ? {
          trial_data: previousContext.trial_data  || null,
          intel_data: previousContext.intel_data  || null,
          fit_score:  previousContext.fit_score   || null,
          rag_context: previousContext.rag_context || null,
        }
      : null,
  };

  const response = await fetch(
    `/api/research/stream/${encodeURIComponent(companyName)}`,
    {
      method:  "POST",
      headers: { "Content-Type": "application/json", ..._authHeader() },
      body:    JSON.stringify(body),
    }
  );

  if (!response.ok) {
    const err = await response.json().catch(() => ({}));
    onError(err.detail || `Request failed (${response.status})`);
    return;
  }

  await _readSSE(response, (event) => {
    if      (event.type === "agent_complete")  onAgentComplete(event.agent, event.data);
    else if (event.type === "synthesis_chunk") { /* streaming handled server-side, ignored here */ }
    else if (event.type === "done")            onDone(event.result);
    else if (event.type === "error")           onError(event.message);
  });
}
