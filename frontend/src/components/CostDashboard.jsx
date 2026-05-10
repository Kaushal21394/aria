import React, { useEffect, useState } from "react";

/**
 * CostDashboard — Phase 4 usage and cost overview.
 *
 * Fetches from GET /admin/usage (per-org) and GET /admin/usage/all (all orgs).
 * Displays:
 *  - Org-level totals (cost, calls, tokens)
 *  - Cost breakdown by agent (bar chart — pure CSS, no charting lib needed)
 *  - Daily spend trend (sparkline dots)
 *  - Cross-org overview table
 */
export default function CostDashboard({ token, orgInfo, onClose }) {
  const [myUsage,  setMyUsage]  = useState(null);
  const [allUsage, setAllUsage] = useState(null);
  const [loading,  setLoading]  = useState(true);
  const [error,    setError]    = useState(null);

  useEffect(() => {
    const headers = { Authorization: `Bearer ${token}` };
    Promise.all([
      fetch("/api/admin/usage",     { headers }).then((r) => r.json()),
      fetch("/api/admin/usage/all", { headers }).then((r) => r.json()),
    ])
      .then(([my, all]) => {
        setMyUsage(my);
        setAllUsage(all);
      })
      .catch((err) => setError(err.message))
      .finally(() => setLoading(false));
  }, [token]);

  return (
    <div className="fixed inset-0 z-50 flex items-start justify-center
      bg-black/60 backdrop-blur-sm overflow-y-auto py-8 px-4">
      <div className="w-full max-w-3xl glass-panel rounded-2xl border border-white/10
        shadow-2xl shadow-cyan-900/20 p-6 flex flex-col gap-6">

        {/* Header */}
        <div className="flex items-center justify-between">
          <div>
            <h2 className="text-lg font-black text-on-surface font-headline">
              Usage &amp; Cost Dashboard
            </h2>
            <p className="text-xs text-on-surface-variant font-data mt-0.5">
              {orgInfo.orgName} · {orgInfo.plan} plan · user: {orgInfo.userId}
            </p>
          </div>
          <button
            onClick={onClose}
            className="text-slate-500 hover:text-on-surface transition text-xl leading-none"
            aria-label="Close"
          >
            ✕
          </button>
        </div>

        {loading && (
          <div className="flex flex-col gap-3">
            {[1, 2, 3].map((i) => (
              <div key={i} className="h-16 rounded-xl bg-surface-container animate-pulse" />
            ))}
          </div>
        )}

        {error && (
          <p className="text-sm text-error bg-error/10 border border-error/20 rounded-lg px-4 py-3">
            {error}
          </p>
        )}

        {myUsage && !loading && (
          <>
            {/* ── Totals ── */}
            <TotalsRow totals={myUsage.totals} />

            {/* ── By agent ── */}
            {myUsage.by_agent?.length > 0 && (
              <Section title="Cost by Agent">
                <AgentBreakdown rows={myUsage.by_agent} />
              </Section>
            )}

            {/* ── Daily trend ── */}
            {myUsage.by_day?.length > 0 && (
              <Section title="Daily Spend Trend">
                <DailyTrend rows={myUsage.by_day} />
              </Section>
            )}

            {/* ── All orgs ── */}
            {allUsage?.length > 0 && (
              <Section title="All Organisations">
                <AllOrgsTable rows={allUsage} currentOrg={orgInfo.orgId} />
              </Section>
            )}

            {myUsage.totals?.total_calls === 0 && (
              <p className="text-sm text-on-surface-variant text-center py-6">
                No usage recorded yet for <span className="text-secondary">{orgInfo.orgName}</span>.
                Run a brief or research query to see cost data here.
              </p>
            )}
          </>
        )}
      </div>
    </div>
  );
}

// ── Sub-components ─────────────────────────────────────────────────────────

function Section({ title, children }) {
  return (
    <div>
      <p className="text-xs font-bold text-secondary uppercase tracking-widest font-data mb-3">
        {title}
      </p>
      {children}
    </div>
  );
}

function TotalsRow({ totals }) {
  if (!totals) return null;
  const cost   = (totals.total_cost  ?? 0).toFixed(6);
  const calls  = totals.total_calls  ?? 0;
  const input  = (totals.total_input  ?? 0).toLocaleString();
  const output = (totals.total_output ?? 0).toLocaleString();

  return (
    <div className="grid grid-cols-2 sm:grid-cols-4 gap-3">
      {[
        { label: "Total Cost",     value: `$${cost}`,   sub: "USD"     },
        { label: "API Calls",      value: calls,         sub: "requests"},
        { label: "Input Tokens",   value: input,         sub: "tokens"  },
        { label: "Output Tokens",  value: output,        sub: "tokens"  },
      ].map(({ label, value, sub }) => (
        <div key={label} className="bg-surface-container rounded-xl p-4 border border-white/5">
          <p className="text-[10px] text-on-surface-variant font-data uppercase tracking-wider mb-1">
            {label}
          </p>
          <p className="text-lg font-black text-on-surface font-headline">{value}</p>
          <p className="text-[10px] text-slate-600 font-data">{sub}</p>
        </div>
      ))}
    </div>
  );
}

function AgentBreakdown({ rows }) {
  const max = Math.max(...rows.map((r) => r.cost), 0.000001);
  return (
    <div className="flex flex-col gap-2">
      {rows.map((r) => {
        const pct = Math.round((r.cost / max) * 100);
        return (
          <div key={r.agent} className="flex items-center gap-3">
            <p className="text-xs text-on-surface-variant font-data w-36 flex-shrink-0 truncate capitalize">
              {r.agent.replace(/_/g, " ")}
            </p>
            <div className="flex-1 bg-surface-container rounded-full h-2 overflow-hidden">
              <div
                className="h-2 rounded-full bg-secondary transition-all duration-500"
                style={{ width: `${pct}%` }}
              />
            </div>
            <p className="text-xs text-on-surface font-data w-24 text-right flex-shrink-0">
              ${r.cost.toFixed(6)}
              <span className="text-slate-600 ml-1">({r.calls})</span>
            </p>
          </div>
        );
      })}
    </div>
  );
}

function DailyTrend({ rows }) {
  const max = Math.max(...rows.map((r) => r.cost), 0.000001);
  return (
    <div className="flex items-end gap-1.5 h-16">
      {rows.map((r) => {
        const h = Math.max(4, Math.round((r.cost / max) * 56));
        return (
          <div
            key={r.day}
            className="flex-1 flex flex-col items-center justify-end gap-1 group"
            title={`${r.day}: $${r.cost.toFixed(6)} (${r.calls} calls)`}
          >
            <div
              className="w-full rounded-t bg-secondary/60 group-hover:bg-secondary transition"
              style={{ height: `${h}px` }}
            />
            <p className="text-[8px] text-slate-600 font-data rotate-45 origin-left hidden sm:block">
              {r.day.slice(5)}
            </p>
          </div>
        );
      })}
    </div>
  );
}

function AllOrgsTable({ rows, currentOrg }) {
  return (
    <div className="overflow-x-auto">
      <table className="w-full text-xs font-data">
        <thead>
          <tr className="text-on-surface-variant uppercase tracking-wider border-b border-white/5">
            <th className="text-left py-2 pr-4 font-bold">Organisation</th>
            <th className="text-left py-2 pr-4 font-bold">Plan</th>
            <th className="text-right py-2 pr-4 font-bold">Total Cost</th>
            <th className="text-right py-2 font-bold">Calls</th>
          </tr>
        </thead>
        <tbody>
          {rows.map((r) => (
            <tr
              key={r.id}
              className={`border-b border-white/5 transition
                ${r.id === currentOrg ? "text-secondary" : "text-on-surface-variant"}`}
            >
              <td className="py-2 pr-4 font-medium">
                {r.name}
                {r.id === currentOrg && (
                  <span className="ml-1.5 text-[9px] bg-secondary/20 text-secondary px-1.5 py-0.5 rounded">
                    you
                  </span>
                )}
              </td>
              <td className="py-2 pr-4 capitalize">{r.plan}</td>
              <td className="py-2 pr-4 text-right">${(r.total_cost ?? 0).toFixed(6)}</td>
              <td className="py-2 text-right">{r.total_calls ?? 0}</td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}
