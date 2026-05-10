import React from "react";

export default function BriefDisplay({ data }) {
  if (!data) return null;
  const { brief, raw_trial_count, sec_filings_found, usage } = data;
  const totalTokens = usage.input_tokens + usage.output_tokens;

  return (
    <div className="flex flex-col gap-4">

      {/* ── Header ── */}
      <div className="glass-panel rounded-xl p-6">
        <div className="flex items-start justify-between gap-4 flex-wrap">
          <div>
            <h2 className="text-2xl font-black text-on-surface font-headline">{brief.company_name}</h2>
            <div className="flex flex-wrap gap-2 mt-3">
              <Badge color="secondary" icon="🧪">{raw_trial_count} active trials</Badge>
              <Badge color="tertiary"  icon="📄">{sec_filings_found} SEC filings</Badge>
              <Badge color="surface"   icon="⚡">{totalTokens.toLocaleString()} tokens</Badge>
            </div>
          </div>
          <span className="text-xs font-data text-on-surface-variant bg-surface-container px-3 py-1.5 rounded-lg border border-white/10">
            {usage.model}
          </span>
        </div>
      </div>

      {/* ── Overview + Trial Activity ── */}
      <div className="grid grid-cols-1 xl:grid-cols-2 gap-4">
        <Card title="Company Overview" icon={<BuildingIcon />}>
          <p className="text-sm text-on-surface-variant leading-relaxed">{brief.company_overview}</p>
        </Card>

        <Card title="Trial Activity" icon={<ChartIcon />}>
          <div className="grid grid-cols-2 gap-3 mb-4">
            <StatTile value={brief.trial_activity.total_active_trials} label="Active Trials" accent />
            {Object.entries(brief.trial_activity.phases).slice(0, 3).map(([phase, count]) => (
              <StatTile key={phase} value={count} label={phase.replace("PHASE", "Phase ")} />
            ))}
          </div>
          <div className="flex flex-col gap-2.5">
            <TagRow label="TAs"  items={brief.trial_activity.therapeutic_areas} color="secondary" />
            <TagRow label="Geo"  items={brief.trial_activity.geographic_spread}  color="tertiary"  />
          </div>
        </Card>
      </div>

      {/* ── Pipeline Summary ── */}
      {brief.pipeline_summary.length > 0 && (
        <Card title="Pipeline Summary" icon={<BeakerIcon />}>
          <div className="overflow-x-auto">
            <table className="w-full text-sm">
              <thead>
                <tr className="border-b border-white/10">
                  {["Phase", "Therapeutic Area", "Trials", "Key Indications"].map((h) => (
                    <th key={h} className="text-left pb-3 pr-4 text-xs font-bold text-on-surface-variant uppercase tracking-wider font-data">
                      {h}
                    </th>
                  ))}
                </tr>
              </thead>
              <tbody className="divide-y divide-white/5">
                {brief.pipeline_summary.map((row, i) => (
                  <tr key={i} className="hover:bg-white/5 transition-colors">
                    <td className="py-3 pr-4"><PhaseBadge phase={row.phase} /></td>
                    <td className="py-3 pr-4 text-on-surface-variant">{row.therapeutic_area ?? "—"}</td>
                    <td className="py-3 pr-4 font-bold text-on-surface font-data">{row.trial_count ?? "—"}</td>
                    <td className="py-3 text-on-surface-variant text-xs leading-relaxed">
                      {(row.key_indications ?? []).join(", ") || "—"}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </Card>
      )}

      {/* ── Signals + Service Areas ── */}
      <div className="grid grid-cols-1 xl:grid-cols-2 gap-4">
        <Card title="Opportunity Signals" icon={<LightbulbIcon />}>
          <ol className="flex flex-col gap-3">
            {brief.opportunity_signals.map((s, i) => (
              <li key={i} className="flex gap-3 text-sm text-on-surface-variant leading-relaxed">
                <span className="text-secondary font-bold tabular-nums flex-shrink-0 text-xs mt-0.5 w-5 font-data">
                  {String(i + 1).padStart(2, "0")}
                </span>
                <span>{s}</span>
              </li>
            ))}
          </ol>
        </Card>

        <Card title="Recommended CRO Service Areas" icon={<TargetIcon />}>
          <div className="flex flex-col gap-2">
            {brief.recommended_service_areas.map((area, i) => (
              <div key={i}
                className="flex items-center gap-2.5 px-3.5 py-2.5 rounded-lg
                  bg-secondary/10 border border-secondary/20
                  text-sm text-on-surface font-medium
                  hover:bg-secondary/15 transition-colors cursor-default">
                <span className="h-1.5 w-1.5 rounded-full bg-secondary flex-shrink-0" />
                {area}
              </div>
            ))}
          </div>
        </Card>
      </div>

    </div>
  );
}

// ── Reusable building blocks ───────────────────────────────────────────────

function Card({ title, icon, children }) {
  return (
    <div className="glass-panel rounded-xl p-5">
      <h3 className="flex items-center gap-2 text-xs font-bold uppercase tracking-widest text-on-surface-variant mb-4 font-data">
        <span className="text-secondary">{icon}</span>
        {title}
      </h3>
      {children}
    </div>
  );
}

function Badge({ color, icon, children }) {
  const styles = {
    secondary: "bg-secondary/10 text-secondary border-secondary/30",
    tertiary:  "bg-tertiary/10  text-tertiary  border-tertiary/30",
    surface:   "bg-surface-container text-on-surface-variant border-outline-variant",
  };
  return (
    <span className={`inline-flex items-center gap-1.5 px-2.5 py-1 rounded-full text-xs font-medium border ${styles[color]}`}>
      {icon} {children}
    </span>
  );
}

function StatTile({ value, label, accent }) {
  return (
    <div className={`rounded-lg p-3 border ${
      accent
        ? "bg-secondary/10 border-secondary/30"
        : "bg-surface-container border-white/10"
    }`}>
      <span className={`text-2xl font-bold tabular-nums block font-data ${accent ? "text-secondary" : "text-on-surface"}`}>
        {value}
      </span>
      <span className="text-xs text-on-surface-variant mt-0.5 block">{label}</span>
    </div>
  );
}

function TagRow({ label, items = [], color }) {
  if (!items.length) return null;
  const styles = {
    secondary: "bg-secondary/10 text-secondary border-secondary/30",
    tertiary:  "bg-tertiary/10  text-tertiary  border-tertiary/30",
  };
  return (
    <div className="flex flex-wrap items-center gap-1.5">
      <span className="text-xs text-on-surface-variant w-7 flex-shrink-0 font-medium font-data">{label}</span>
      {items.map((item, i) => (
        <span key={i} className={`text-xs px-2 py-0.5 rounded-full border ${styles[color] ?? styles.secondary}`}>
          {item}
        </span>
      ))}
    </div>
  );
}

const PHASE_STYLES = {
  PHASE1:       "bg-sky-500/10     text-sky-400     border-sky-500/30",
  PHASE2:       "bg-violet-500/10  text-violet-400  border-violet-500/30",
  PHASE3:       "bg-amber-500/10   text-amber-400   border-amber-500/30",
  PHASE4:       "bg-emerald-500/10 text-emerald-400 border-emerald-500/30",
  EARLY_PHASE1: "bg-cyan-500/10    text-cyan-400    border-cyan-500/30",
};

function PhaseBadge({ phase }) {
  const style = PHASE_STYLES[phase] ?? "bg-surface-container text-on-surface-variant border-outline-variant";
  const label = phase ? phase.replace("PHASE", "Phase ").replace("_", " ") : "N/A";
  return (
    <span className={`inline-block text-xs font-bold px-2.5 py-1 rounded-full border font-data ${style}`}>
      {label}
    </span>
  );
}

// ── Icons ──────────────────────────────────────────────────────────────────

const P = { className: "h-4 w-4", fill: "none", stroke: "currentColor", strokeWidth: 1.75, viewBox: "0 0 24 24" };

function BuildingIcon() {
  return <svg {...P}><path strokeLinecap="round" strokeLinejoin="round" d="M3.75 21h16.5M4.5 3h15M5.25 3v18m13.5-18v18M9 6.75h1.5m-1.5 3h1.5m-1.5 3h1.5m3-6H15m-1.5 3H15m-1.5 3H15M9 21v-3.375c0-.621.504-1.125 1.125-1.125h3.75c.621 0 1.125.504 1.125 1.125V21" /></svg>;
}
function ChartIcon() {
  return <svg {...P}><path strokeLinecap="round" strokeLinejoin="round" d="M3 13.125C3 12.504 3.504 12 4.125 12h2.25c.621 0 1.125.504 1.125 1.125v6.75C7.5 20.496 6.996 21 6.375 21h-2.25A1.125 1.125 0 013 19.875v-6.75zM9.75 8.625c0-.621.504-1.125 1.125-1.125h2.25c.621 0 1.125.504 1.125 1.125v11.25c0 .621-.504 1.125-1.125 1.125h-2.25a1.125 1.125 0 01-1.125-1.125V8.625zM16.5 4.125c0-.621.504-1.125 1.125-1.125h2.25C20.496 3 21 3.504 21 4.125v15.75c0 .621-.504 1.125-1.125 1.125h-2.25a1.125 1.125 0 01-1.125-1.125V4.125z" /></svg>;
}
function BeakerIcon() {
  return <svg {...P}><path strokeLinecap="round" strokeLinejoin="round" d="M9.75 3.104v5.714a2.25 2.25 0 01-.659 1.591L5 14.5M9.75 3.104c-.251.023-.501.05-.75.082m.75-.082a24.301 24.301 0 014.5 0m0 0v5.714c0 .597.237 1.17.659 1.591L19.8 15.3M14.25 3.104c.251.023.501.05.75.082M19.8 15.3l-1.57.393A9.065 9.065 0 0112 15a9.065 9.065 0 00-6.23-.693L5 14.5m14.8.8l1.402 1.402c1 1 .03 2.798-1.442 2.798H6.24c-1.47 0-2.441-1.798-1.442-2.798L5 14.5" /></svg>;
}
function LightbulbIcon() {
  return <svg {...P}><path strokeLinecap="round" strokeLinejoin="round" d="M12 18v-5.25m0 0a6.01 6.01 0 001.5-.189m-1.5.189a6.01 6.01 0 01-1.5-.189m3.75 7.478a12.06 12.06 0 01-4.5 0m3.75 2.383a14.406 14.406 0 01-3 0M14.25 18v-.192c0-.983.658-1.823 1.508-2.316a7.5 7.5 0 10-7.517 0c.85.493 1.509 1.333 1.509 2.316V18" /></svg>;
}
function TargetIcon() {
  return <svg {...P}><path strokeLinecap="round" strokeLinejoin="round" d="M15.59 14.37a6 6 0 01-5.84 7.38v-4.8m5.84-2.58a14.98 14.98 0 006.16-12.12A14.98 14.98 0 009.631 8.41m5.96 5.96a14.926 14.926 0 01-5.841 2.58m-.119-8.54a6 6 0 00-7.381 5.84h4.8m2.581-5.84a14.927 14.927 0 00-2.58 5.84m2.699 2.7c-.103.021-.207.041-.311.06a15.09 15.09 0 01-2.448-2.448 14.9 14.9 0 01.06-.312m-2.24 2.39a4.493 4.493 0 00-1.757 4.306 4.493 4.493 0 004.306-1.758M16.5 9a1.5 1.5 0 11-3 0 1.5 1.5 0 013 0z" /></svg>;
}
