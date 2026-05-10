import React, { useState } from "react";
import BriefDisplay from "./BriefDisplay";
import ResearchDisplay from "./ResearchDisplay";

/**
 * ChatMessage — renders a single turn in the conversation.
 *
 * User bubbles: simple right-aligned text.
 * Assistant bubbles: left-aligned text + optional inline result card
 *                    (BriefDisplay or ResearchDisplay, collapsed by default).
 */
export default function ChatMessage({ message }) {
  const { role, content, result_type, result_data } = message;
  const isUser = role === "user";

  return (
    <div className={`flex ${isUser ? "justify-end" : "justify-start"} mb-4`}>
      {!isUser && <AssistantAvatar />}
      <div className={`flex flex-col gap-2 max-w-[80%] ${isUser ? "items-end" : "items-start"}`}>
        {/* Text bubble */}
        {content && (
          <div className={`rounded-2xl px-4 py-3 text-sm leading-relaxed
            ${isUser
              ? "bg-secondary text-on-secondary rounded-br-sm"
              : "bg-surface-container text-on-surface rounded-bl-sm border border-white/10"
            }`}
          >
            {content}
          </div>
        )}

        {/* Inline result card — collapsed by default */}
        {result_data && (
          <ResultCard resultType={result_type} resultData={result_data} />
        )}
      </div>
      {isUser && <UserAvatar />}
    </div>
  );
}

// ── Streaming / in-progress assistant message ──────────────────────────────

export function AssistantStreamMessage({ streamingText, emailText, phase }) {
  return (
    <div className="flex justify-start mb-4">
      <AssistantAvatar />
      <div className="flex flex-col gap-2 max-w-[80%] items-start">

        {/* Status pill during tool execution */}
        {phase && (
          <div className="flex items-center gap-2 px-3 py-1.5 rounded-full
            bg-surface-container border border-secondary/20 text-xs text-secondary font-data">
            <span className="h-1.5 w-1.5 rounded-full bg-secondary animate-pulse flex-shrink-0" />
            {phase}
          </div>
        )}

        {/* Live email preview — streams while the drafter node runs */}
        {emailText && (
          <div className="w-full rounded-xl border border-violet-400/20 bg-violet-400/5 overflow-hidden">
            <div className="flex items-center gap-2 px-4 py-2 border-b border-violet-400/10">
              <span className="text-[10px] font-bold uppercase tracking-widest font-data text-violet-400">
                ✉ Writing outreach email
              </span>
              <span className="h-1.5 w-1.5 rounded-full bg-violet-400 animate-pulse ml-auto" />
            </div>
            <pre className="px-4 py-3 text-xs text-on-surface-variant font-mono whitespace-pre-wrap
              leading-relaxed max-h-48 overflow-y-auto">
              {emailText}
              <span className="inline-block w-0.5 h-3 bg-violet-400 ml-0.5 animate-pulse" />
            </pre>
          </div>
        )}

        {/* Streaming assistant commentary */}
        {streamingText && (
          <div className="rounded-2xl rounded-bl-sm px-4 py-3 text-sm leading-relaxed
            bg-surface-container text-on-surface border border-white/10">
            {streamingText}
            <span className="inline-block w-0.5 h-3.5 bg-secondary ml-0.5 animate-pulse" />
          </div>
        )}

        {/* Empty thinking dots */}
        {!streamingText && !emailText && !phase && (
          <div className="rounded-2xl rounded-bl-sm px-4 py-3
            bg-surface-container border border-white/10 flex gap-1.5">
            {[0, 1, 2].map((i) => (
              <span
                key={i}
                className="h-1.5 w-1.5 rounded-full bg-slate-500 animate-bounce"
                style={{ animationDelay: `${i * 0.15}s` }}
              />
            ))}
          </div>
        )}
      </div>
    </div>
  );
}

// ── Collapsible result card ────────────────────────────────────────────────

function ResultCard({ resultType, resultData }) {
  const [expanded, setExpanded] = useState(false);

  const label = resultType === "research" ? "Research Report" : "Company Brief";
  const icon  = resultType === "research" ? "📊" : "📄";

  return (
    <div className="w-full rounded-xl border border-secondary/20 bg-surface-container overflow-hidden">
      {/* Header — always visible, click to expand */}
      <button
        onClick={() => setExpanded((v) => !v)}
        className="w-full flex items-center justify-between px-4 py-3 hover:bg-white/5 transition"
      >
        <span className="flex items-center gap-2 text-sm font-bold text-secondary font-headline">
          <span>{icon}</span>
          {label}
          {resultType === "research" && resultData?.fit_score?.total_score != null && (
            <span className="text-xs font-data font-normal text-on-surface-variant ml-1">
              Fit score: <span className="text-secondary font-bold">
                {resultData.fit_score.total_score}/100
              </span>
            </span>
          )}
        </span>
        <svg
          className={`h-4 w-4 text-slate-500 transition-transform ${expanded ? "rotate-180" : ""}`}
          fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}
        >
          <path strokeLinecap="round" strokeLinejoin="round" d="M19 9l-7 7-7-7" />
        </svg>
      </button>

      {/* Expanded full result */}
      {expanded && (
        <div className="border-t border-white/10 p-2">
          {resultType === "research" && <ResearchDisplay data={resultData} />}
          {resultType === "brief"    && <BriefDisplay    data={resultData} />}
        </div>
      )}
    </div>
  );
}

// ── Avatars ────────────────────────────────────────────────────────────────

function AssistantAvatar() {
  return (
    <div className="h-7 w-7 rounded-full bg-gradient-to-br from-cyan-500 to-violet-600
      flex items-center justify-center flex-shrink-0 mr-2 mt-1 text-[10px] font-black text-white
      shadow-lg shadow-cyan-900/30">
      A
    </div>
  );
}

function UserAvatar() {
  return (
    <div className="h-7 w-7 rounded-full bg-surface-container border border-white/10
      flex items-center justify-center flex-shrink-0 ml-2 mt-1 text-[10px] text-slate-400">
      U
    </div>
  );
}
