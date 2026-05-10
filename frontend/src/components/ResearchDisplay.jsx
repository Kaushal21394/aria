import React, { useState } from "react";

// ── Fit dimension metadata ─────────────────────────────────────────────────

const DIM_META = {
  therapeutic_area_match: { label: "Therapeutic Area", weight: "30%" },
  phase_capability:       { label: "Phase Capability",  weight: "25%" },
  geographic_overlap:     { label: "Geographic Overlap", weight: "20%" },
  deal_size_fit:          { label: "Deal Size Fit",      weight: "15%" },
  competitive_timing:     { label: "Competitive Timing", weight: "10%" },
};

const DIM_ORDER = Object.keys(DIM_META);

// ── Score colour helpers ───────────────────────────────────────────────────

function scoreColor(score) {
  if (score >= 80) return { stroke: "#4fdbc8", text: "text-secondary",  bar: "bg-secondary",  label: "Strong Fit",   badge: "bg-secondary/10 text-secondary border-secondary/30"   };
  if (score >= 60) return { stroke: "#22d3ee", text: "text-cyan-400",   bar: "bg-cyan-400",   label: "Good Fit",     badge: "bg-cyan-400/10  text-cyan-400  border-cyan-400/30"    };
  if (score >= 40) return { stroke: "#f59e0b", text: "text-amber-400",  bar: "bg-amber-400",  label: "Moderate Fit", badge: "bg-amber-400/10 text-amber-400 border-amber-400/30"   };
  return              { stroke: "#ffb4ab", text: "text-error",      bar: "bg-error",      label: "Weak Fit",     badge: "bg-error/10     text-error     border-error/30"        };
}

// ── Root component ─────────────────────────────────────────────────────────

// ── Output format metadata ─────────────────────────────────────────────────

const FORMAT_META = {
  outreach_email:    { label: "BD Outreach Email",   icon: <MailIcon />,      accent: "tertiary"  },
  competitive_brief: { label: "Competitive Brief",   icon: <ChartBarIcon />,  accent: "secondary" },
  pipeline_summary:  { label: "Pipeline Summary",    icon: <ListIcon />,      accent: "cyan"      },
  account_snapshot:  { label: "Account Snapshot",    icon: <UserIcon />,      accent: "violet"    },
};

const ACCENT_CLASSES = {
  tertiary:  { border: "border-l-tertiary",  text: "text-tertiary",  bg: "bg-tertiary/10  border-tertiary/30"  },
  secondary: { border: "border-l-secondary", text: "text-secondary", bg: "bg-secondary/10 border-secondary/30" },
  cyan:      { border: "border-l-cyan-400",  text: "text-cyan-400",  bg: "bg-cyan-400/10  border-cyan-400/30"  },
  violet:    { border: "border-l-violet-400",text: "text-violet-400",bg: "bg-violet-400/10 border-violet-400/30"},
};

export default function ResearchDisplay({ data }) {
  if (!data) return null;
  const { company_name, goal, execution_plan, trial_data, intel_data, fit_score, rag_context, synthesis, mcp_actions, errors, total_usage } = data;

  const totalTokens = (total_usage || []).reduce(
    (sum, u) => sum + (u.input_tokens || 0) + (u.output_tokens || 0), 0
  );
  const score      = fit_score?.total_score ?? 0;
  const colors     = scoreColor(score);
  const hasFit     = fit_score && Object.keys(fit_score).length > 0 && score > 0;
  const hasTrial   = trial_data && (trial_data.total_count ?? 0) > 0;
  const hasIntel   = intel_data && Object.values(intel_data).some(v => Array.isArray(v) && v.length > 0);
  const outputFmt  = execution_plan?.output_format || "outreach_email";
  const fmtMeta    = FORMAT_META[outputFmt] || FORMAT_META.outreach_email;

  return (
    <div className="flex flex-col gap-4">

      {/* ── Header ── */}
      <div className="glass-panel rounded-xl p-6">
        <div className="flex items-center justify-between flex-wrap gap-4">
          <div>
            <h2 className="text-2xl font-black text-on-surface font-headline">{company_name}</h2>
            {goal && (
              <p className="text-sm text-on-surface-variant mt-1 italic max-w-xl">"{goal}"</p>
            )}
            <div className="flex flex-wrap items-center gap-2 mt-3">
              {hasFit && (
                <span className={`inline-flex items-center gap-1.5 px-3 py-1 rounded-full text-sm font-bold border ${colors.badge}`}>
                  {score} / 100 · {colors.label}
                </span>
              )}
              {hasTrial && (
                <span className="inline-flex items-center gap-1.5 px-2.5 py-1 rounded-full text-xs font-medium border bg-surface-container text-on-surface-variant border-white/10">
                  {trial_data.total_count} active trials
                </span>
              )}
              <span className="inline-flex items-center gap-1.5 px-2.5 py-1 rounded-full text-xs font-medium border bg-surface-container text-on-surface-variant border-white/10">
                {totalTokens.toLocaleString()} tokens
              </span>
            </div>
          </div>

          {/* Execution plan badge */}
          <div className="flex flex-col items-end gap-2">
            <span className={`inline-flex items-center gap-1.5 text-xs font-bold px-3 py-1.5 rounded-lg border font-data
              ${ACCENT_CLASSES[fmtMeta.accent]?.bg || "bg-surface-container text-on-surface-variant border-white/10"}`}>
              <span className={ACCENT_CLASSES[fmtMeta.accent]?.text}>{fmtMeta.icon}</span>
              {fmtMeta.label}
            </span>
            {execution_plan?.agents?.length > 0 && (
              <span className="text-[10px] text-on-surface-variant font-data">
                Agents: {execution_plan.agents.join(" · ")}
              </span>
            )}
          </div>
        </div>

        {/* Planner rationale */}
        {execution_plan?.rationale && (
          <p className="mt-3 pt-3 border-t border-white/10 text-xs text-on-surface-variant/70 font-data italic">
            Planner: {execution_plan.rationale}
          </p>
        )}
      </div>

      {/* ── Fit Score + Trial Stats (conditional on data) ── */}
      {(hasFit || hasTrial) && (
        <div className={`grid gap-4 ${hasFit && hasTrial ? "grid-cols-1 xl:grid-cols-2" : "grid-cols-1"}`}>
          {hasFit  && <FitScoreCard score={score} colors={colors} dimensions={fit_score?.dimensions} summary={fit_score?.summary} />}
          {hasTrial && <TrialStatsCard trialData={trial_data} />}
        </div>
      )}

      {/* ── Intelligence Signals (conditional) ── */}
      {hasIntel && <IntelCard intelData={intel_data} />}

      {/* ── RAG Context (outreach_email only) ── */}
      {rag_context?.length > 0 && <RAGContextCard hits={rag_context} outputFormat={outputFmt} />}

      {/* ── Synthesis output ── */}
      {synthesis && <SynthesisCard synthesis={synthesis} outputFormat={outputFmt} fmtMeta={fmtMeta} ragGrounded={rag_context?.length > 0} />}

      {/* ── MCP Actions (outreach_email only) ── */}
      {mcp_actions?.length > 0 && <MCPActionsCard actions={mcp_actions} />}

      {/* ── Agent Usage ── */}
      {total_usage?.length > 0 && <UsageCard usage={total_usage} />}

      {/* ── Errors ── */}
      {errors?.length > 0 && <ErrorsCard errors={errors} />}

    </div>
  );
}

// ── Fit Score card ─────────────────────────────────────────────────────────

function FitScoreCard({ score, colors, dimensions = {}, summary }) {
  const radius = 88;
  const circ   = 2 * Math.PI * radius;
  const offset = circ * (1 - score / 100);

  return (
    <Card title="CRO Fit Score" icon={<TargetIcon />}>
      <div className="flex flex-col gap-5">
        <div className="flex items-center gap-6">
          {/* SVG ring — matches stitch design */}
          <div className="relative h-40 w-40 flex-shrink-0">
            <svg className="h-full w-full -rotate-90" viewBox="0 0 192 192">
              <circle cx="96" cy="96" r={radius} fill="transparent"
                stroke="rgba(255,255,255,0.08)" strokeWidth="8" />
              <circle cx="96" cy="96" r={radius} fill="transparent"
                stroke={colors.stroke} strokeWidth="12" strokeLinecap="round"
                strokeDasharray={circ} strokeDashoffset={offset}
                style={{ transition: "stroke-dashoffset 0.5s ease" }}
              />
            </svg>
            <div className="absolute inset-0 flex flex-col items-center justify-center">
              <span className={`text-4xl font-bold tabular-nums font-data ${colors.text}`}>{score}</span>
              <span className="text-xs text-on-surface-variant font-data">{colors.label}</span>
            </div>
          </div>
          <div className="flex-1">
            {summary && <p className="text-sm text-on-surface-variant leading-relaxed">{summary}</p>}
          </div>
        </div>

        <div className="flex flex-col gap-3 pt-2 border-t border-white/10">
          {DIM_ORDER.map((key) => (
            <DimensionBar key={key} dimKey={key} data={dimensions[key]} />
          ))}
        </div>
      </div>
    </Card>
  );
}

function DimensionBar({ dimKey, data }) {
  const meta  = DIM_META[dimKey];
  const score = data?.score ?? 0;
  const c     = scoreColor(score);

  return (
    <div className="flex flex-col gap-1">
      <div className="flex items-center justify-between gap-3">
        <span className="text-xs font-medium text-on-surface-variant">{meta?.label}</span>
        <div className="flex items-center gap-2">
          <span className="text-xs text-on-surface-variant font-data">{meta?.weight}</span>
          <span className={`text-sm font-bold tabular-nums w-6 text-right font-data ${c.text}`}>{score}</span>
        </div>
      </div>
      <div className="h-1.5 bg-surface-container-highest rounded-full overflow-hidden">
        <div className={`h-full rounded-full transition-all duration-500 ${c.bar}`} style={{ width: `${score}%` }} />
      </div>
      {data?.rationale && (
        <p className="text-xs text-on-surface-variant leading-relaxed">{data.rationale}</p>
      )}
    </div>
  );
}

// ── Trial Stats card ───────────────────────────────────────────────────────

const PHASE_CONFIG = {
  EARLY_PHASE1: { bar: "#22d3ee", bg: "bg-cyan-400",   text: "text-cyan-400"   },
  PHASE1:       { bar: "#818cf8", bg: "bg-indigo-400", text: "text-indigo-400" },
  PHASE2:       { bar: "#a78bfa", bg: "bg-violet-400", text: "text-violet-400" },
  PHASE3:       { bar: "#f59e0b", bg: "bg-amber-400",  text: "text-amber-400"  },
  PHASE4:       { bar: "#4fdbc8", bg: "bg-secondary",  text: "text-secondary"  },
};
const DEFAULT_PHASE = { bar: "#768497", bg: "bg-slate-500", text: "text-slate-400" };

function phaseLabel(key) {
  return key.replace("EARLY_PHASE", "Early Ph.").replace("PHASE", "Phase ");
}

function TrialStatsCard({ trialData = {} }) {
  const { total_count = 0, phases = {}, conditions = [] } = trialData;
  const phaseEntries    = Object.entries(phases).sort((a, b) => b[1] - a[1]);
  const maxCount        = Math.max(...phaseEntries.map(([, c]) => c), 1);
  const stackedSegments = phaseEntries.map(([phase, count]) => ({
    phase, count,
    pct: total_count > 0 ? (count / total_count) * 100 : 0,
    config: PHASE_CONFIG[phase] ?? DEFAULT_PHASE,
    label: phaseLabel(phase),
  }));
  const topConditions = conditions.slice(0, 8);

  return (
    <Card title="Trial Activity" icon={<ChartIcon />}>
      <div className="flex flex-col gap-5">

        {/* Headline stat */}
        <div className="flex items-center gap-4">
          <div className="bg-secondary/10 border border-secondary/30 rounded-xl px-5 py-3 text-center flex-shrink-0">
            <span className="text-4xl font-bold text-secondary tabular-nums font-data">{total_count}</span>
            <p className="text-xs text-on-surface-variant mt-0.5 font-data">Active Trials</p>
          </div>

          {stackedSegments.length > 0 && (
            <div className="flex-1 flex flex-col gap-2">
              <p className="text-xs font-bold text-on-surface-variant uppercase tracking-widest font-data">Phase Distribution</p>
              <div className="flex h-6 rounded-full overflow-hidden gap-px">
                {stackedSegments.map(({ phase, pct, config }) => (
                  <div key={phase} style={{ width: `${pct}%`, backgroundColor: config.bar }}
                    title={`${phaseLabel(phase)}: ${Math.round(pct)}%`}
                    className="transition-all duration-500" />
                ))}
              </div>
              <div className="flex flex-wrap gap-2">
                {stackedSegments.map(({ phase, count, config, label }) => (
                  <div key={phase} className="flex items-center gap-1.5">
                    <span className={`h-2.5 w-2.5 rounded-sm flex-shrink-0 ${config.bg}`} />
                    <span className="text-xs text-on-surface-variant">{label}</span>
                    <span className="text-xs font-bold text-on-surface tabular-nums font-data">{count}</span>
                  </div>
                ))}
              </div>
            </div>
          )}
        </div>

        {/* Phase bar chart */}
        {phaseEntries.length > 0 && (
          <div className="flex flex-col gap-2 pt-1 border-t border-white/10">
            <p className="text-xs font-bold text-on-surface-variant uppercase tracking-widest mb-1 font-data">Trials by Phase</p>
            {phaseEntries.map(([phase, count]) => {
              const cfg = PHASE_CONFIG[phase] ?? DEFAULT_PHASE;
              const pct = (count / maxCount) * 100;
              return (
                <div key={phase} className="flex items-center gap-3">
                  <span className={`text-xs font-medium w-20 flex-shrink-0 font-data ${cfg.text}`}>
                    {phaseLabel(phase)}
                  </span>
                  <div className="flex-1 h-5 bg-surface-container-highest rounded overflow-hidden">
                    <div className="h-full rounded transition-all duration-500 flex items-center justify-end pr-2"
                      style={{ width: `${pct}%`, backgroundColor: cfg.bar }}>
                      <span className="text-white text-xs font-bold font-data">{count}</span>
                    </div>
                  </div>
                </div>
              );
            })}
          </div>
        )}

        {/* Top conditions */}
        {topConditions.length > 0 && (
          <div className="pt-1 border-t border-white/10">
            <p className="text-xs font-bold text-on-surface-variant uppercase tracking-widest mb-2 font-data">Top Conditions</p>
            <div className="flex flex-col gap-1.5">
              {topConditions.map((c, i) => {
                const pct = 100 - (i / topConditions.length) * 60;
                return (
                  <div key={i} className="flex items-center gap-2">
                    <span className="text-xs text-on-surface-variant w-40 truncate flex-shrink-0" title={c}>{c}</span>
                    <div className="flex-1 h-2 bg-surface-container-highest rounded-full overflow-hidden">
                      <div className="h-full bg-secondary/50 rounded-full transition-all duration-500"
                        style={{ width: `${pct}%` }} />
                    </div>
                  </div>
                );
              })}
            </div>
          </div>
        )}

      </div>
    </Card>
  );
}

// ── Intelligence Signals card ──────────────────────────────────────────────

function IntelCard({ intelData = {} }) {
  const { key_signals = [], recent_news = [], pipeline_updates = [], cro_partnership_indicators = [] } = intelData;

  const sections = [
    { title: "Key BD Signals",        items: key_signals,                color: "secondary" },
    { title: "Pipeline Updates",       items: pipeline_updates,           color: "tertiary"  },
    { title: "CRO Partnership Clues",  items: cro_partnership_indicators, color: "amber"     },
  ];

  const colorMap = {
    secondary: { dot: "bg-secondary", text: "text-secondary", bg: "bg-secondary/5  border-secondary/15" },
    tertiary:  { dot: "bg-tertiary",  text: "text-tertiary",  bg: "bg-tertiary/5   border-tertiary/15"  },
    amber:     { dot: "bg-amber-400", text: "text-amber-400", bg: "bg-amber-400/5  border-amber-400/15" },
  };

  return (
    <Card title="Intelligence Signals" icon={<LightbulbIcon />}>
      <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
        {sections.map(({ title, items, color }) => {
          const c = colorMap[color];
          return (
            <div key={title} className={`rounded-lg border p-4 ${c.bg}`}>
              <p className={`text-xs font-bold uppercase tracking-widest mb-3 font-data ${c.text}`}>{title}</p>
              {items.length > 0 ? (
                <ul className="flex flex-col gap-2.5">
                  {items.map((item, i) => (
                    <li key={i} className="flex gap-2 text-sm text-on-surface-variant leading-relaxed">
                      <span className={`h-1.5 w-1.5 rounded-full flex-shrink-0 mt-1.5 ${c.dot}`} />
                      {item}
                    </li>
                  ))}
                </ul>
              ) : (
                <p className="text-xs text-on-surface-variant italic">No data available</p>
              )}
            </div>
          );
        })}
      </div>

      {recent_news.length > 0 && (
        <div className="mt-4 pt-4 border-t border-white/10">
          <p className="text-xs font-bold text-on-surface-variant uppercase tracking-widest mb-2 font-data">Recent News</p>
          <ul className="flex flex-col gap-1.5">
            {recent_news.map((n, i) => (
              <li key={i} className="flex gap-2 text-sm text-on-surface-variant leading-relaxed">
                <span className="text-secondary flex-shrink-0">·</span>
                {n}
              </li>
            ))}
          </ul>
        </div>
      )}
    </Card>
  );
}

// ── Lightweight markdown renderer ─────────────────────────────────────────

function renderInline(text, keyPrefix = "") {
  const parts = [];
  const regex = /\*\*([^*]+)\*\*|\*([^*]+)\*/g;
  let last = 0, match, idx = 0;
  while ((match = regex.exec(text)) !== null) {
    if (match.index > last) parts.push(text.slice(last, match.index));
    if (match[1] !== undefined)
      parts.push(<strong key={`${keyPrefix}-b${idx++}`} className="font-semibold text-on-surface">{match[1]}</strong>);
    else
      parts.push(<em key={`${keyPrefix}-i${idx++}`} className="italic">{match[2]}</em>);
    last = match.index + match[0].length;
  }
  if (last < text.length) parts.push(text.slice(last));
  return parts.length > 1 ? parts : text;
}

function MarkdownBody({ text, isEmail }) {
  if (!text) return null;

  if (isEmail) {
    // Emails are plain text — preserve newlines, render inline bold/italic only
    return (
      <div className="font-mono text-sm text-on-surface-variant leading-relaxed whitespace-pre-wrap">
        {text}
      </div>
    );
  }

  const lines = text.split("\n");
  const out = [];
  let listBuf = [], orderedBuf = [], k = 0;

  function flushList() {
    if (!listBuf.length) return;
    out.push(
      <ul key={k++} className="space-y-1.5 my-2 pl-1">
        {listBuf.map((item, i) => (
          <li key={i} className="flex gap-2.5 text-sm text-on-surface-variant leading-relaxed">
            <span className="text-secondary flex-shrink-0 select-none mt-[3px]">·</span>
            <span>{renderInline(item, `ul-${k}-${i}`)}</span>
          </li>
        ))}
      </ul>
    );
    listBuf = [];
  }
  function flushOrdered() {
    if (!orderedBuf.length) return;
    out.push(
      <ol key={k++} className="space-y-1.5 my-2 pl-1">
        {orderedBuf.map((item, i) => (
          <li key={i} className="flex gap-2.5 text-sm text-on-surface-variant leading-relaxed">
            <span className="text-secondary font-bold font-data flex-shrink-0 w-5 text-right select-none">{i + 1}.</span>
            <span>{renderInline(item, `ol-${k}-${i}`)}</span>
          </li>
        ))}
      </ol>
    );
    orderedBuf = [];
  }

  for (const line of lines) {
    if (/^#{1,2}\s/.test(line)) {
      flushList(); flushOrdered();
      const level = line.match(/^(#+)/)[1].length;
      const content = line.replace(/^#+\s/, "");
      out.push(
        level === 1
          ? <h2 key={k++} className="text-base font-bold text-on-surface mt-5 mb-1.5 pb-1.5 border-b border-white/10 first:mt-0">{renderInline(content, `h2-${k}`)}</h2>
          : <h3 key={k++} className="text-sm font-bold text-on-surface mt-4 mb-1 first:mt-0">{renderInline(content, `h3-${k}`)}</h3>
      );
    } else if (/^### /.test(line)) {
      flushList(); flushOrdered();
      out.push(<h4 key={k++} className="text-xs font-bold text-on-surface-variant uppercase tracking-widest mt-3 mb-1 font-data">{line.slice(4)}</h4>);
    } else if (/^[-*] /.test(line)) {
      flushOrdered();
      listBuf.push(line.slice(2));
    } else if (/^\d+\.\s/.test(line)) {
      flushList();
      orderedBuf.push(line.replace(/^\d+\.\s/, ""));
    } else if (line.trim() === "---" || line.trim() === "***") {
      flushList(); flushOrdered();
      out.push(<hr key={k++} className="border-white/10 my-4" />);
    } else if (line.trim() === "") {
      flushList(); flushOrdered();
    } else {
      flushList(); flushOrdered();
      out.push(
        <p key={k++} className="text-sm text-on-surface-variant leading-relaxed mb-1.5">
          {renderInline(line, `p-${k}`)}
        </p>
      );
    }
  }
  flushList(); flushOrdered();
  return <div className="space-y-0.5">{out}</div>;
}

// ── Synthesis output card (adaptive per output format) ────────────────────

function SynthesisCard({ synthesis, outputFormat, fmtMeta, ragGrounded }) {
  const [copied, setCopied] = useState(false);
  const accent  = ACCENT_CLASSES[fmtMeta.accent] || ACCENT_CLASSES.secondary;
  const isEmail = outputFormat === "outreach_email";

  function handleCopy() {
    navigator.clipboard.writeText(synthesis).then(() => {
      setCopied(true);
      setTimeout(() => setCopied(false), 2000);
    });
  }

  return (
    <div className={`glass-panel rounded-xl p-5 border-l-4 ${accent.border}`}>
      {/* Header row */}
      <div className="flex items-center justify-between mb-4 flex-wrap gap-2">
        <h3 className="flex items-center gap-2 text-xs font-bold uppercase tracking-widest text-on-surface-variant font-data">
          <span className={accent.text}>{fmtMeta.icon}</span>
          {fmtMeta.label}
          {isEmail && ragGrounded && (
            <span className="normal-case tracking-normal font-medium px-2 py-0.5 rounded-full text-xs
              bg-secondary/10 text-secondary border border-secondary/30">
              RAG-grounded
            </span>
          )}
        </h3>
        <button
          onClick={handleCopy}
          className={`flex items-center gap-1.5 px-3 py-1.5 rounded-lg text-xs font-medium border
            transition-colors duration-150 ${accent.bg} ${accent.text}`}
        >
          {copied
            ? <svg className="h-3.5 w-3.5" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2.5}><path strokeLinecap="round" strokeLinejoin="round" d="M5 13l4 4L19 7" /></svg>
            : <svg className="h-3.5 w-3.5" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}><path strokeLinecap="round" strokeLinejoin="round" d="M8 16H6a2 2 0 01-2-2V6a2 2 0 012-2h8a2 2 0 012 2v2m-6 12h8a2 2 0 002-2v-8a2 2 0 00-2-2h-8a2 2 0 00-2 2v8a2 2 0 002 2z" /></svg>
          }
          {copied ? "Copied!" : "Copy"}
        </button>
      </div>

      {/* Content body */}
      <div className={`rounded-lg border border-white/10 p-5 ${isEmail ? "bg-surface-container-high" : "bg-surface-container"}`}>
        <MarkdownBody text={synthesis} isEmail={isEmail} />
      </div>
    </div>
  );
}

// ── RAG Context card (Phase 3) ────────────────────────────────────────────

const TA_STYLE = {
  oncology:          "bg-violet-500/10 text-violet-400 border-violet-500/30",
  rare_disease:      "bg-purple-500/10 text-purple-400 border-purple-500/30",
  neurology:         "bg-indigo-500/10 text-indigo-400 border-indigo-500/30",
  cardiology:        "bg-red-500/10    text-red-400    border-red-500/30",
  metabolic:         "bg-amber-500/10  text-amber-400  border-amber-500/30",
  respiratory:       "bg-cyan-500/10   text-cyan-400   border-cyan-500/30",
  immunology:        "bg-emerald-500/10 text-emerald-400 border-emerald-500/30",
  infectious_disease:"bg-orange-500/10 text-orange-400 border-orange-500/30",
};
const TA_DEFAULT = "bg-slate-500/10 text-slate-400 border-slate-500/30";

const OUTCOME_STYLE = {
  won:     "bg-secondary/10 text-secondary border-secondary/30",
  lost:    "bg-error/10     text-error     border-error/30",
  ongoing: "bg-amber-400/10 text-amber-400 border-amber-400/30",
};

function RAGContextCard({ hits, outputFormat }) {
  const desc = outputFormat === "outreach_email"
    ? `The outreach email was grounded in these ${hits.length} past studies from the Meridian CRO knowledge base.`
    : `${hits.length} relevant past proposals retrieved from the CRO knowledge base.`;
  return (
    <Card title="Retrieved Proposals · RAG Context" icon={<DatabaseIcon />}>
      <p className="text-xs text-on-surface-variant mb-4 -mt-2">{desc}</p>
      <div className="grid grid-cols-1 md:grid-cols-3 gap-3">
        {hits.map((hit, i) => <ProposalHitCard key={i} hit={hit} rank={i + 1} />)}
      </div>
    </Card>
  );
}

function ProposalHitCard({ hit, rank }) {
  const [expanded, setExpanded] = useState(false);

  const ta       = hit.therapeutic_area || "";
  const taLabel  = ta.replace(/_/g, " ").replace(/\b\w/g, c => c.toUpperCase());
  const taStyle  = TA_STYLE[ta] || TA_DEFAULT;
  const outcome  = (hit.outcome || "").toLowerCase();
  const outcomeStyle = OUTCOME_STYLE[outcome] || TA_DEFAULT;
  const scorePct = Math.round((hit.score || 0) * 100);
  const preview  = hit.text?.slice(0, 180);
  const hasMore  = (hit.text?.length || 0) > 180;

  return (
    <div className="flex flex-col gap-3 rounded-lg border border-white/10 bg-surface-container p-4">

      {/* Rank + proposal ID */}
      <div className="flex items-center justify-between gap-2">
        <span className="text-xs font-bold text-on-surface-variant font-data">#{rank}</span>
        <span className="text-xs text-on-surface-variant/50 font-data truncate">{hit.proposal_id}</span>
      </div>

      {/* TA + outcome badges */}
      <div className="flex flex-wrap gap-1.5">
        <span className={`text-xs font-medium px-2 py-0.5 rounded-full border ${taStyle}`}>{taLabel}</span>
        <span className={`text-xs font-medium px-2 py-0.5 rounded-full border ${outcomeStyle}`}>
          {outcome.toUpperCase()}
        </span>
        <span className="text-xs font-medium px-2 py-0.5 rounded-full border bg-surface-container-highest text-on-surface-variant border-white/10">
          {hit.phase}
        </span>
      </div>

      {/* Geography + year */}
      <div className="flex items-center gap-2 text-xs text-on-surface-variant/70 font-data">
        <span>{(hit.geography || "").replace(/_/g, " ").replace(/\b\w/g, c => c.toUpperCase())}</span>
        <span>·</span>
        <span>{hit.year}</span>
      </div>

      {/* Relevance score bar */}
      <div className="flex flex-col gap-1">
        <div className="flex items-center justify-between">
          <span className="text-xs text-on-surface-variant/50">Relevance</span>
          <span className="text-xs font-bold text-secondary tabular-nums font-data">{scorePct}%</span>
        </div>
        <div className="h-1.5 bg-surface-container-highest rounded-full overflow-hidden">
          <div
            className="h-full bg-secondary rounded-full transition-all duration-500"
            style={{ width: `${scorePct}%` }}
          />
        </div>
      </div>

      {/* Proposal text (collapsible) */}
      <div className="text-xs text-on-surface-variant leading-relaxed">
        {expanded ? hit.text : `${preview}${hasMore ? "…" : ""}`}
      </div>
      {hasMore && (
        <button
          onClick={() => setExpanded(e => !e)}
          className="text-xs text-secondary hover:text-secondary/80 text-left transition-colors"
        >
          {expanded ? "Show less" : "Show full proposal"}
        </button>
      )}
    </div>
  );
}

// ── Phase 4: MCP actions card ──────────────────────────────────────────────

const MCP_META = {
  draft_gmail_email:    { label: "Gmail Draft",      icon: "✉", color: "text-sky-400",    bg: "bg-sky-400/10  border-sky-400/20"  },
  create_calendar_event:{ label: "Calendar Event",   icon: "📅", color: "text-violet-400", bg: "bg-violet-400/10 border-violet-400/20" },
};

function MCPActionsCard({ actions }) {
  return (
    <div className="glass-panel rounded-xl p-5">
      <p className="text-xs font-bold text-on-surface-variant uppercase tracking-widest mb-4 font-data flex items-center gap-2">
        <span className="text-secondary">⚡</span>
        MCP Actions — Gmail &amp; Calendar
      </p>
      <div className="flex flex-col gap-3">
        {actions.map((action, i) => {
          const meta   = MCP_META[action.tool] ?? { label: action.tool, icon: "🔧", color: "text-secondary", bg: "bg-secondary/10 border-secondary/20" };
          const result = action.result ?? {};
          return (
            <div key={i} className={`rounded-xl border p-4 ${meta.bg}`}>
              <div className="flex items-center gap-2 mb-2">
                <span className="text-base">{meta.icon}</span>
                <span className={`text-xs font-bold uppercase tracking-wider font-data ${meta.color}`}>
                  {meta.label}
                </span>
                {result.status === "ok" && (
                  <span className="ml-auto text-[10px] font-data font-bold text-secondary bg-secondary/10 px-1.5 py-0.5 rounded">
                    DONE
                  </span>
                )}
              </div>
              <p className="text-xs text-on-surface-variant font-data leading-relaxed">
                {result.message ?? "Action executed."}
              </p>

              {/* Gmail-specific details */}
              {action.tool === "draft_gmail_email" && action.input && (
                <div className="mt-2 text-[11px] text-slate-500 font-data space-y-0.5">
                  <p><span className="text-slate-400">To:</span> {action.input.to}</p>
                  <p><span className="text-slate-400">Subject:</span> {action.input.subject}</p>
                </div>
              )}

              {/* Calendar-specific details */}
              {action.tool === "create_calendar_event" && action.input && (
                <div className="mt-2 text-[11px] text-slate-500 font-data space-y-0.5">
                  <p><span className="text-slate-400">Date:</span> {action.input.proposed_date}</p>
                  <p><span className="text-slate-400">Duration:</span> {action.input.duration_minutes} min</p>
                  {result.meet_link && (
                    <p className="text-violet-400 truncate">{result.meet_link}</p>
                  )}
                </div>
              )}
            </div>
          );
        })}
      </div>
    </div>
  );
}

// ── Agent usage breakdown ──────────────────────────────────────────────────

function UsageCard({ usage }) {
  const total = usage.reduce((s, u) => s + (u.input_tokens || 0) + (u.output_tokens || 0), 0);
  return (
    <div className="glass-panel rounded-xl p-5">
      <div className="flex items-center justify-between flex-wrap gap-4">
        <p className="text-xs font-bold text-on-surface-variant uppercase tracking-widest font-data">Agent Token Usage</p>
        <span className="text-xs text-on-surface-variant font-data">{total.toLocaleString()} total tokens</span>
      </div>
      <div className="flex flex-wrap gap-3 mt-3">
        {usage.map((u, i) => {
          const t     = (u.input_tokens || 0) + (u.output_tokens || 0);
          const label = (u.agent || "").replace(/_/g, " ").replace(/\b\w/g, c => c.toUpperCase());
          return (
            <div key={i} className="flex items-center gap-2 px-3 py-1.5 bg-surface-container border border-white/10 rounded-lg text-xs">
              <span className="text-on-surface-variant">{label}</span>
              <span className="font-bold text-on-surface tabular-nums font-data">{t.toLocaleString()}</span>
            </div>
          );
        })}
      </div>
    </div>
  );
}

// ── Errors card ────────────────────────────────────────────────────────────

function ErrorsCard({ errors }) {
  return (
    <div className="glass-panel rounded-xl p-4 border-l-4 border-amber-400">
      <p className="text-xs font-bold text-amber-400 uppercase tracking-widest mb-2 font-data">Agent Warnings</p>
      <ul className="flex flex-col gap-1">
        {errors.map((e, i) => (
          <li key={i} className="text-sm text-on-surface-variant">· {e}</li>
        ))}
      </ul>
    </div>
  );
}

// ── Shared Card shell ──────────────────────────────────────────────────────

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

// ── Icons ──────────────────────────────────────────────────────────────────

const P = { className: "h-4 w-4", fill: "none", stroke: "currentColor", strokeWidth: 1.75, viewBox: "0 0 24 24" };

function TargetIcon() {
  return <svg {...P}><path strokeLinecap="round" strokeLinejoin="round" d="M15.59 14.37a6 6 0 01-5.84 7.38v-4.8m5.84-2.58a14.98 14.98 0 006.16-12.12A14.98 14.98 0 009.631 8.41m5.96 5.96a14.926 14.926 0 01-5.841 2.58m-.119-8.54a6 6 0 00-7.381 5.84h4.8m2.581-5.84a14.927 14.927 0 00-2.58 5.84m2.699 2.7c-.103.021-.207.041-.311.06a15.09 15.09 0 01-2.448-2.448 14.9 14.9 0 01.06-.312m-2.24 2.39a4.493 4.493 0 00-1.757 4.306 4.493 4.493 0 004.306-1.758M16.5 9a1.5 1.5 0 11-3 0 1.5 1.5 0 013 0z" /></svg>;
}
function ChartIcon() {
  return <svg {...P}><path strokeLinecap="round" strokeLinejoin="round" d="M3 13.125C3 12.504 3.504 12 4.125 12h2.25c.621 0 1.125.504 1.125 1.125v6.75C7.5 20.496 6.996 21 6.375 21h-2.25A1.125 1.125 0 013 19.875v-6.75zM9.75 8.625c0-.621.504-1.125 1.125-1.125h2.25c.621 0 1.125.504 1.125 1.125v11.25c0 .621-.504 1.125-1.125 1.125h-2.25a1.125 1.125 0 01-1.125-1.125V8.625zM16.5 4.125c0-.621.504-1.125 1.125-1.125h2.25C20.496 3 21 3.504 21 4.125v15.75c0 .621-.504 1.125-1.125 1.125h-2.25a1.125 1.125 0 01-1.125-1.125V4.125z" /></svg>;
}
function LightbulbIcon() {
  return <svg {...P}><path strokeLinecap="round" strokeLinejoin="round" d="M12 18v-5.25m0 0a6.01 6.01 0 001.5-.189m-1.5.189a6.01 6.01 0 01-1.5-.189m3.75 7.478a12.06 12.06 0 01-4.5 0m3.75 2.383a14.406 14.406 0 01-3 0M14.25 18v-.192c0-.983.658-1.823 1.508-2.316a7.5 7.5 0 10-7.517 0c.85.493 1.509 1.333 1.509 2.316V18" /></svg>;
}
function MailIcon() {
  return <svg {...P}><path strokeLinecap="round" strokeLinejoin="round" d="M21.75 6.75v10.5a2.25 2.25 0 01-2.25 2.25h-15a2.25 2.25 0 01-2.25-2.25V6.75m19.5 0A2.25 2.25 0 0019.5 4.5h-15a2.25 2.25 0 00-2.25 2.25m19.5 0v.243a2.25 2.25 0 01-1.07 1.916l-7.5 4.615a2.25 2.25 0 01-2.36 0L3.32 8.91a2.25 2.25 0 01-1.07-1.916V6.75" /></svg>;
}
function DatabaseIcon() {
  return <svg {...P}><path strokeLinecap="round" strokeLinejoin="round" d="M20.25 6.375c0 2.278-3.694 4.125-8.25 4.125S3.75 8.653 3.75 6.375m16.5 0c0-2.278-3.694-4.125-8.25-4.125S3.75 4.097 3.75 6.375m16.5 0v11.25c0 2.278-3.694 4.125-8.25 4.125s-8.25-1.847-8.25-4.125V6.375m16.5 2.25c0 2.278-3.694 4.125-8.25 4.125s-8.25-1.847-8.25-4.125m16.5 4.5c0 2.278-3.694 4.125-8.25 4.125s-8.25-1.847-8.25-4.125" /></svg>;
}
function ChartBarIcon() {
  return <svg {...P}><path strokeLinecap="round" strokeLinejoin="round" d="M7.5 14.25v2.25m3-4.5v4.5m3-6.75v6.75m3-9v9M6 20.25h12A2.25 2.25 0 0020.25 18V6A2.25 2.25 0 0018 3.75H6A2.25 2.25 0 003.75 6v12A2.25 2.25 0 006 20.25z" /></svg>;
}
function ListIcon() {
  return <svg {...P}><path strokeLinecap="round" strokeLinejoin="round" d="M8.25 6.75h12M8.25 12h12m-12 5.25h12M3.75 6.75h.007v.008H3.75V6.75zm.375 0a.375.375 0 11-.75 0 .375.375 0 01.75 0zM3.75 12h.007v.008H3.75V12zm.375 0a.375.375 0 11-.75 0 .375.375 0 01.75 0zm-.375 5.25h.007v.008H3.75v-.008zm.375 0a.375.375 0 11-.75 0 .375.375 0 01.75 0z" /></svg>;
}
function UserIcon() {
  return <svg {...P}><path strokeLinecap="round" strokeLinejoin="round" d="M15.75 6a3.75 3.75 0 11-7.5 0 3.75 3.75 0 017.5 0zM4.501 20.118a7.5 7.5 0 0114.998 0A17.933 17.933 0 0112 21.75c-2.676 0-5.216-.584-7.499-1.632z" /></svg>;
}
