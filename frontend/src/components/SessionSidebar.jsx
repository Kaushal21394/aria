import React from "react";

/**
 * SessionSidebar — lists past conversations and lets the user start a new one.
 *
 * Props:
 *   sessions        [{ id, title, updated_at }]
 *   activeSessionId  string | null
 *   onSelect(id)     switch to an existing session
 *   onNew()          create + switch to a new session
 *   onDelete(id)     delete a session
 *   loading          bool — sessions are being fetched
 */
export default function SessionSidebar({
  sessions,
  activeSessionId,
  onSelect,
  onNew,
  onDelete,
  loading,
}) {
  return (
    <aside className="flex flex-col h-full w-64 flex-shrink-0
      bg-slate-950/80 border-r border-white/10">

      {/* Header */}
      <div className="px-4 py-4 border-b border-white/10 flex items-center justify-between">
        <span className="text-xs font-bold text-on-surface-variant uppercase tracking-widest font-data">
          Conversations
        </span>
        <button
          onClick={onNew}
          title="New conversation"
          className="h-7 w-7 rounded-lg bg-secondary/10 border border-secondary/20
            flex items-center justify-center text-secondary hover:bg-secondary/20 transition"
        >
          <svg className="h-3.5 w-3.5" fill="none" viewBox="0 0 24 24"
            stroke="currentColor" strokeWidth={2.5}>
            <path strokeLinecap="round" strokeLinejoin="round" d="M12 4v16m8-8H4" />
          </svg>
        </button>
      </div>

      {/* Session list */}
      <div className="flex-1 overflow-y-auto py-2">
        {loading && (
          <div className="flex flex-col gap-2 px-3 pt-2">
            {[1, 2, 3].map((i) => (
              <div key={i} className="h-10 rounded-lg bg-surface-container animate-pulse" />
            ))}
          </div>
        )}

        {!loading && sessions.length === 0 && (
          <p className="text-xs text-slate-600 text-center px-4 pt-6 font-data leading-relaxed">
            No conversations yet.<br />Click + to start one.
          </p>
        )}

        {!loading && sessions.map((s) => (
          <SessionItem
            key={s.id}
            session={s}
            active={s.id === activeSessionId}
            onSelect={() => onSelect(s.id)}
            onDelete={(e) => { e.stopPropagation(); onDelete(s.id); }}
          />
        ))}
      </div>
    </aside>
  );
}

function SessionItem({ session, active, onSelect, onDelete }) {
  const date = new Date(session.updated_at + "Z").toLocaleDateString(undefined, {
    month: "short", day: "numeric",
  });

  return (
    <button
      onClick={onSelect}
      className={`group w-full text-left px-3 py-2.5 mx-0 flex items-start gap-2 transition
        rounded-lg mx-1 ${active
          ? "bg-secondary/10 border border-secondary/20"
          : "hover:bg-surface-container border border-transparent"
        }`}
      style={{ width: "calc(100% - 8px)" }}
    >
      <svg className={`h-3.5 w-3.5 flex-shrink-0 mt-0.5 ${active ? "text-secondary" : "text-slate-600"}`}
        fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={1.75}>
        <path strokeLinecap="round" strokeLinejoin="round"
          d="M8.625 12a.375.375 0 11-.75 0 .375.375 0 01.75 0zm0 0H8.25m4.125 0a.375.375 0 11-.75 0 .375.375 0 01.75 0zm0 0H12m4.125 0a.375.375 0 11-.75 0 .375.375 0 01.75 0zm0 0h-.375M21 12c0 4.556-4.03 8.25-9 8.25a9.764 9.764 0 01-2.555-.337A5.972 5.972 0 015.41 20.97a5.969 5.969 0 01-.474-.065 4.48 4.48 0 00.978-2.025c.09-.457-.133-.901-.467-1.226C3.93 16.178 3 14.189 3 12c0-4.556 4.03-8.25 9-8.25s9 3.694 9 8.25z" />
      </svg>
      <div className="flex-1 min-w-0">
        <p className={`text-xs font-medium truncate ${active ? "text-on-surface" : "text-on-surface-variant"}`}>
          {session.title}
        </p>
        <p className="text-[10px] text-slate-600 font-data mt-0.5">{date}</p>
      </div>
      {/* Delete button — only visible on hover */}
      <button
        onClick={onDelete}
        className="opacity-0 group-hover:opacity-100 transition text-slate-600
          hover:text-error flex-shrink-0 p-0.5 rounded"
        title="Delete"
      >
        <svg className="h-3 w-3" fill="none" viewBox="0 0 24 24"
          stroke="currentColor" strokeWidth={2}>
          <path strokeLinecap="round" strokeLinejoin="round" d="M6 18L18 6M6 6l12 12" />
        </svg>
      </button>
    </button>
  );
}
