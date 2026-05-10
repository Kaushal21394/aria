import React, { useEffect, useRef, useState } from "react";
import ChatMessage, { AssistantStreamMessage } from "./ChatMessage";
import SessionSidebar from "./SessionSidebar";
import {
  createSession,
  deleteSession,
  getHistory,
  listSessions,
  streamMessage,
} from "../api/client";

const AGENT_LABELS = {
  trial_agent:      "Fetching clinical trial data…",
  intel_agent:      "Gathering market intelligence…",
  fit_scorer:       "Scoring CRO fit…",
  outreach_drafter: "Drafting outreach email…",
};

const SUGGESTED_PROMPTS = [
  "Research Pfizer and draft a BD outreach email",
  "Give me a quick brief on Novartis",
  "Research AstraZeneca focusing on oncology",
  "What CRO services would fit Moderna best?",
];

export default function ChatWindow({ orgInfo }) {
  // ── Session state ──────────────────────────────────────────────────────
  const [sessions,         setSessions]         = useState([]);
  const [activeSessionId,  setActiveSessionId]  = useState(null);
  const [sessionsLoading,  setSessionsLoading]  = useState(true);

  // ── Message state ──────────────────────────────────────────────────────
  const [messages,   setMessages]   = useState([]);   // persisted messages
  const [input,      setInput]      = useState("");
  const [sending,    setSending]    = useState(false);

  // ── Streaming / in-progress state ─────────────────────────────────────
  const [streamText,  setStreamText]  = useState("");
  const [emailText,   setEmailText]   = useState(""); // outreach email tokens
  const [phase,       setPhase]       = useState(null); // status label shown during tool use

  const bottomRef  = useRef(null);
  const inputRef   = useRef(null);

  // ── Load sessions on mount ─────────────────────────────────────────────
  useEffect(() => {
    listSessions()
      .then((s) => {
        setSessions(s);
        // Auto-open the most recent session if one exists
        if (s.length > 0) loadSession(s[0].id);
      })
      .catch(console.error)
      .finally(() => setSessionsLoading(false));
  }, []);

  // ── Auto-scroll to bottom ──────────────────────────────────────────────
  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages, streamText, phase]);

  // ── Session management ─────────────────────────────────────────────────
  async function loadSession(sessionId) {
    setActiveSessionId(sessionId);
    setMessages([]);
    setStreamText("");
    setPhase(null);
    try {
      const history = await getHistory(sessionId);
      setMessages(history);
    } catch (e) {
      console.error(e);
    }
  }

  async function handleNewSession() {
    try {
      const session = await createSession();
      setSessions((prev) => [session, ...prev]);
      setActiveSessionId(session.id);
      setMessages([]);
      setStreamText("");
      setPhase(null);
      inputRef.current?.focus();
    } catch (e) {
      console.error(e);
    }
  }

  async function handleDeleteSession(sessionId) {
    await deleteSession(sessionId);
    setSessions((prev) => prev.filter((s) => s.id !== sessionId));
    if (activeSessionId === sessionId) {
      const remaining = sessions.filter((s) => s.id !== sessionId);
      if (remaining.length > 0) {
        loadSession(remaining[0].id);
      } else {
        setActiveSessionId(null);
        setMessages([]);
      }
    }
  }

  // ── Send a message ─────────────────────────────────────────────────────
  async function handleSend(text) {
    const content = (text ?? input).trim();
    if (!content || sending) return;

    // If no session exists yet, create one first
    let sessionId = activeSessionId;
    if (!sessionId) {
      const session = await createSession();
      setSessions((prev) => [session, ...prev]);
      setActiveSessionId(session.id);
      sessionId = session.id;
    }

    setInput("");
    setSending(true);
    setStreamText("");
    setEmailText("");
    setPhase(null);

    // Optimistically add user message to the list
    const userMsg = { id: Date.now(), role: "user", content, result_type: null, result_data: null, created_at: new Date().toISOString() };
    setMessages((prev) => [...prev, userMsg]);

    await streamMessage(sessionId, content, {
      onThinking:   ()             => setPhase("ARIA is thinking…"),
      onToolStart:  (tool)         => setPhase(`Running ${tool === "run_research" ? "full research pipeline" : "brief generator"}…`),
      onAgentStep:  (agent)        => setPhase(AGENT_LABELS[agent] ?? `${agent}…`),
      onEmailChunk: (text)         => { setEmailText((prev) => prev + text); setPhase("Writing outreach email…"); },
      onToolDone:   ()             => { setPhase("Composing reply…"); setEmailText(""); },
      onTextChunk:  (text)         => setStreamText((prev) => prev + text),
      onDone: (text, resultType, result) => {
        const assistantMsg = {
          id:          Date.now() + 1,
          role:        "assistant",
          content:     text,
          result_type: resultType,
          result_data: result,
          created_at:  new Date().toISOString(),
        };
        setMessages((prev) => [...prev, assistantMsg]);
        setStreamText("");
        setEmailText("");
        setPhase(null);
        setSending(false);

        // Update session title in sidebar (the backend auto-sets it from first message)
        listSessions().then(setSessions).catch(() => {});
      },
      onError: (msg) => {
        const errMsg = {
          id:       Date.now() + 1,
          role:     "assistant",
          content:  `Sorry, something went wrong: ${msg}`,
          result_type: null, result_data: null,
          created_at: new Date().toISOString(),
        };
        setMessages((prev) => [...prev, errMsg]);
        setStreamText("");
        setEmailText("");
        setPhase(null);
        setSending(false);
      },
    });
  }

  function handleKeyDown(e) {
    if (e.key === "Enter" && !e.shiftKey) {
      e.preventDefault();
      handleSend();
    }
  }

  const showWelcome = !activeSessionId || messages.length === 0;

  return (
    <div className="flex h-full min-h-0">
      {/* ── Sidebar ── */}
      <SessionSidebar
        sessions={sessions}
        activeSessionId={activeSessionId}
        onSelect={loadSession}
        onNew={handleNewSession}
        onDelete={handleDeleteSession}
        loading={sessionsLoading}
      />

      {/* ── Main chat area ── */}
      <div className="flex flex-col flex-1 min-w-0 min-h-0">

        {/* Message list */}
        <div className="flex-1 overflow-y-auto px-6 py-6">

          {/* Welcome / empty state */}
          {showWelcome && (
            <div className="flex flex-col items-center justify-center h-full gap-8 py-12">
              <div className="text-center">
                <p className="text-2xl font-black text-on-surface font-headline mb-2">
                  What would you like to research?
                </p>
                <p className="text-sm text-on-surface-variant max-w-md">
                  Ask me to research a pharma sponsor, score CRO fit,
                  or draft a BD outreach email. I'll run the right pipeline automatically.
                </p>
              </div>

              {/* Suggested prompts */}
              <div className="grid grid-cols-1 sm:grid-cols-2 gap-3 w-full max-w-xl">
                {SUGGESTED_PROMPTS.map((prompt) => (
                  <button
                    key={prompt}
                    onClick={() => handleSend(prompt)}
                    className="text-left px-4 py-3 rounded-xl bg-surface-container border border-white/10
                      text-xs text-on-surface-variant hover:border-secondary/30 hover:text-on-surface
                      hover:bg-surface-container-high transition leading-relaxed"
                  >
                    {prompt}
                  </button>
                ))}
              </div>
            </div>
          )}

          {/* Messages */}
          {messages.map((msg) => (
            <ChatMessage key={msg.id} message={msg} />
          ))}

          {/* Streaming in-progress message */}
          {sending && (
            <AssistantStreamMessage streamingText={streamText} emailText={emailText} phase={phase} />
          )}

          <div ref={bottomRef} />
        </div>

        {/* ── Input bar ── */}
        <div className="border-t border-white/10 bg-slate-950/80 px-4 py-3 flex-shrink-0">
          <div className="flex items-end gap-3 max-w-4xl mx-auto">
            <textarea
              ref={inputRef}
              value={input}
              onChange={(e) => setInput(e.target.value)}
              onKeyDown={handleKeyDown}
              placeholder="Research a sponsor, ask a follow-up, or request a brief…"
              rows={1}
              disabled={sending}
              className="flex-1 resize-none rounded-xl bg-surface-container border border-white/10
                text-on-surface text-sm px-4 py-3 focus:outline-none focus:border-secondary/40
                focus:ring-1 focus:ring-secondary/20 transition placeholder:text-slate-600
                disabled:opacity-50 max-h-32 leading-relaxed"
              style={{ fieldSizing: "content" }}
            />
            <button
              onClick={() => handleSend()}
              disabled={sending || !input.trim()}
              className="h-10 w-10 rounded-xl bg-secondary flex items-center justify-center
                hover:bg-secondary/90 transition disabled:opacity-40 disabled:cursor-not-allowed
                flex-shrink-0 shadow-lg shadow-cyan-900/30"
            >
              {sending
                ? <span className="h-3 w-3 rounded-full border-2 border-on-secondary/30 border-t-on-secondary animate-spin" />
                : <SendIcon />
              }
            </button>
          </div>
          <p className="text-[10px] text-slate-700 text-center mt-2 font-data">
            Enter to send · Shift+Enter for new line · Results appear inline
          </p>
        </div>
      </div>
    </div>
  );
}

function SendIcon() {
  return (
    <svg className="h-4 w-4 text-on-secondary" fill="none" viewBox="0 0 24 24"
      stroke="currentColor" strokeWidth={2}>
      <path strokeLinecap="round" strokeLinejoin="round"
        d="M6 12L3.269 3.126A59.768 59.768 0 0121.485 12 59.77 59.77 0 013.27 20.876L5.999 12zm0 0h7.5" />
    </svg>
  );
}
