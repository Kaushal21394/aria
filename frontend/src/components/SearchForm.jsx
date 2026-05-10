import React, { useState, useRef, useEffect } from "react";

export const WORKFLOW_STEPS = [
  { step: 1, format: "account_snapshot",  label: "Account Snapshot",  value: "Quick account snapshot for a BD call"                       },
  { step: 2, format: "pipeline_summary",  label: "Pipeline Summary",  value: "Give me a pipeline summary of their active clinical trials"  },
  { step: 3, format: "competitive_brief", label: "Competitive Brief", value: "Write a competitive landscape brief"                         },
  { step: 4, format: "outreach_email",    label: "Outreach Email",    value: "Draft a personalised outreach email to their BD team"        },
];

// ── Filter definitions ─────────────────────────────────────────────────────

const TA_CHIPS = [
  { label: "Oncology",          value: "oncology"          },
  { label: "Rare Disease",      value: "rare_disease"      },
  { label: "Neurology",         value: "neurology"         },
  { label: "Cardiology",        value: "cardiology"        },
  { label: "Metabolic",         value: "metabolic"         },
  { label: "Respiratory",       value: "respiratory"       },
  { label: "Immunology",        value: "immunology"        },
  { label: "Infectious Disease",value: "infectious_disease"},
];

const PHASE_CHIPS = [
  { label: "Phase I",    value: "Phase I"    },
  { label: "Phase I/II", value: "Phase I/II" },
  { label: "Phase II",   value: "Phase II"   },
  { label: "Phase III",  value: "Phase III"  },
];

const GEO_CHIPS = [
  { label: "North America", value: "north_america" },
  { label: "Europe",        value: "europe"        },
  { label: "Asia Pacific",  value: "asia_pacific"  },
  { label: "Global",        value: "global"        },
];

// ── Main component ─────────────────────────────────────────────────────────

export default function SearchForm({ onSearch, loading, filters, onFiltersChange, initialCompany }) {
  const [company,     setCompany]     = useState("");
  const [goal,        setGoal]        = useState("");
  const [filtersOpen, setFiltersOpen] = useState(false);
  const [nameError,   setNameError]   = useState(false);

  const goalRef = useRef(null);
  const nameRef = useRef(null);

  useEffect(() => {
    if (initialCompany) setCompany(initialCompany);
  }, [initialCompany]);

  const isResearch    = goal.trim().length > 0;
  const activeFilters = Object.values(filters || {}).filter(Boolean).length;

  // Auto-resize textarea
  useEffect(() => {
    if (goalRef.current) {
      goalRef.current.style.height = "auto";
      goalRef.current.style.height = goalRef.current.scrollHeight + "px";
    }
  }, [goal]);

  // Close filter panel when switching to quick-brief mode
  useEffect(() => {
    if (!isResearch) setFiltersOpen(false);
  }, [isResearch]);

  function handleSubmit(e) {
    e.preventDefault();
    if (loading) return;
    const trimmed = company.trim();
    if (!trimmed) {
      setNameError(true);
      nameRef.current?.focus();
      return;
    }
    setNameError(false);
    setFiltersOpen(false);
    onSearch(trimmed, goal.trim(), filters);
  }

  function toggleFilter(group, value) {
    onFiltersChange(prev => ({
      ...prev,
      [group]: prev[group] === value ? undefined : value,
    }));
  }

  return (
    <form onSubmit={handleSubmit} className="w-full">
      <div className="glass-panel rounded-2xl">

        {/* ── Company name ── */}
        <div className={`px-4 pt-4 pb-3 transition-colors ${nameError ? "bg-red-500/5" : ""}`}>
          <input
            ref={nameRef}
            type="text"
            value={company}
            onChange={(e) => { setCompany(e.target.value); if (nameError) setNameError(false); }}
            disabled={loading}
            placeholder="Company name — e.g. Novo Nordisk, AstraZeneca…"
            className="w-full bg-transparent text-on-surface placeholder-on-surface-variant/50
              text-sm focus:outline-none disabled:opacity-60 disabled:cursor-not-allowed"
          />
          {nameError && (
            <p className="text-xs text-red-400 mt-1.5">Enter a company name to continue.</p>
          )}
        </div>

        {/* ── Divider ── */}
        <div className="h-px bg-white/8 mx-4" />

        {/* ── Goal textarea ── */}
        <div className="px-4 pt-3 pb-2">
          <textarea
            ref={goalRef}
            rows={1}
            value={goal}
            onChange={(e) => setGoal(e.target.value)}
            onKeyDown={(e) => { if ((e.metaKey || e.ctrlKey) && e.key === "Enter") handleSubmit(e); }}
            disabled={loading}
            placeholder="What do you need? (optional — leave blank for a quick BD brief)"
            className="w-full bg-transparent text-on-surface placeholder-on-surface-variant/50
              text-sm focus:outline-none disabled:opacity-60 disabled:cursor-not-allowed
              resize-none leading-relaxed"
          />

          {/* Workflow step chips — visible when goal is empty */}
          {!goal.trim() && !loading && (
            <div className="flex flex-wrap gap-1.5 mt-2.5">
              {WORKFLOW_STEPS.map((s) => (
                <button
                  key={s.format}
                  type="button"
                  onClick={() => { setGoal(s.value); goalRef.current?.focus(); }}
                  className="inline-flex items-center gap-1.5 px-2.5 py-1 rounded-full text-xs border
                    bg-surface-container-highest border-white/10 text-on-surface-variant
                    hover:border-secondary/40 hover:text-secondary transition-all duration-150"
                >
                  <span className="flex-shrink-0 h-4 w-4 rounded-full bg-surface-container border border-white/15
                    text-[9px] font-bold font-data text-on-surface-variant flex items-center justify-center">
                    {s.step}
                  </span>
                  {s.label}
                </button>
              ))}
            </div>
          )}
        </div>

        {/* ── Filter panel ── */}
        {isResearch && filtersOpen && (
          <div className="mx-4 mb-3 rounded-xl border border-white/10 bg-surface-container overflow-hidden">
            <FilterGroup
              label="Therapeutic Area"
              chips={TA_CHIPS}
              selected={filters?.therapeutic_area}
              onToggle={(v) => toggleFilter("therapeutic_area", v)}
            />
            <div className="border-t border-white/8">
              <FilterGroup
                label="Phase"
                chips={PHASE_CHIPS}
                selected={filters?.phase}
                onToggle={(v) => toggleFilter("phase", v)}
              />
            </div>
            <div className="border-t border-white/8">
              <FilterGroup
                label="Geography"
                chips={GEO_CHIPS}
                selected={filters?.geography}
                onToggle={(v) => toggleFilter("geography", v)}
              />
            </div>
            {activeFilters > 0 && (
              <div className="border-t border-white/8 px-3 py-2 flex justify-end">
                <button
                  type="button"
                  onClick={() => onFiltersChange({})}
                  className="text-xs text-on-surface-variant hover:text-on-surface transition-colors"
                >
                  Clear all
                </button>
              </div>
            )}
          </div>
        )}

        {/* ── Toolbar ── */}
        <div className="flex items-center justify-between px-3 pb-3 pt-2 gap-2">

          {/* Left: mode badge + filters */}
          <div className="flex items-center gap-2 flex-wrap">

            {/* Auto-mode badge — passive indicator, not clickable */}
            <span className={`inline-flex items-center gap-1.5 px-2.5 py-1 rounded-lg text-xs font-medium border font-data select-none
              ${isResearch
                ? "bg-secondary/10 border-secondary/30 text-secondary"
                : "bg-surface-container border-white/10 text-on-surface-variant"
              }`}>
              {isResearch ? <ResearchIcon /> : <BriefIcon />}
              {isResearch ? "Research Agent" : "Quick Brief"}
            </span>

            {/* Filter toggle — research mode only */}
            {isResearch && (
              <button
                type="button"
                onClick={() => setFiltersOpen((o) => !o)}
                disabled={loading}
                className={`flex items-center gap-1.5 px-2.5 py-1 rounded-lg text-xs font-medium border
                  transition-all duration-150 disabled:opacity-50 select-none
                  ${filtersOpen || activeFilters > 0
                    ? "bg-secondary/10 border-secondary/30 text-secondary"
                    : "bg-surface-container border-white/10 text-on-surface-variant hover:bg-surface-container-high hover:text-on-surface"
                  }`}
              >
                <FilterIcon />
                Filters
                {activeFilters > 0 && (
                  <span className="h-4 w-4 rounded-full bg-secondary text-on-secondary text-[10px] font-bold
                    flex items-center justify-center">
                    {activeFilters}
                  </span>
                )}
              </button>
            )}

            {/* Active filter chips (collapsed state) */}
            {isResearch && !filtersOpen && activeFilters > 0 && (
              <div className="flex flex-wrap gap-1">
                {filters?.therapeutic_area && (
                  <ActiveBadge
                    label={TA_CHIPS.find(c => c.value === filters.therapeutic_area)?.label}
                    onRemove={() => toggleFilter("therapeutic_area", filters.therapeutic_area)}
                  />
                )}
                {filters?.phase && (
                  <ActiveBadge
                    label={filters.phase}
                    onRemove={() => toggleFilter("phase", filters.phase)}
                  />
                )}
                {filters?.geography && (
                  <ActiveBadge
                    label={GEO_CHIPS.find(c => c.value === filters.geography)?.label}
                    onRemove={() => toggleFilter("geography", filters.geography)}
                  />
                )}
              </div>
            )}
          </div>

          {/* Submit button */}
          <button
            type="submit"
            disabled={loading}
            className="flex items-center gap-1.5 px-4 py-1.5 rounded-lg flex-shrink-0
              bg-gradient-to-tl from-secondary-container to-secondary
              text-white text-sm font-bold shadow-lg shadow-secondary/20
              disabled:opacity-50 disabled:cursor-not-allowed
              transition-all duration-150 active:scale-[0.98]"
          >
            {loading ? (
              <>
                <svg className="animate-spin h-4 w-4" fill="none" viewBox="0 0 24 24">
                  <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" />
                  <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4z" />
                </svg>
                Working…
              </>
            ) : (
              <>
                {isResearch ? "Run" : "Generate Brief"}
                <ArrowIcon />
              </>
            )}
          </button>

        </div>
      </div>
    </form>
  );
}

// ── Filter sub-components ──────────────────────────────────────────────────

function FilterGroup({ label, chips, selected, onToggle }) {
  return (
    <div className="px-3 py-2.5">
      <p className="text-[10px] font-bold uppercase tracking-widest text-on-surface-variant mb-2 font-data">
        {label}
      </p>
      <div className="flex flex-wrap gap-1.5">
        {chips.map((chip) => {
          const active = selected === chip.value;
          return (
            <button
              key={chip.value}
              type="button"
              onClick={() => onToggle(chip.value)}
              className={`px-2.5 py-1 rounded-full text-xs font-medium border transition-all duration-150
                ${active
                  ? "bg-secondary/15 border-secondary/40 text-secondary"
                  : "bg-surface-container-highest border-white/10 text-on-surface-variant hover:border-white/20 hover:text-on-surface"
                }`}
            >
              {chip.label}
            </button>
          );
        })}
      </div>
    </div>
  );
}

function ActiveBadge({ label, onRemove }) {
  if (!label) return null;
  return (
    <span className="inline-flex items-center gap-1 px-2 py-0.5 rounded-full text-xs font-medium
      bg-secondary/10 border border-secondary/30 text-secondary">
      {label}
      <button
        type="button"
        onClick={onRemove}
        className="hover:text-secondary/60 transition-colors leading-none"
        aria-label={`Remove ${label} filter`}
      >
        ×
      </button>
    </span>
  );
}

// ── Icons ──────────────────────────────────────────────────────────────────

function BriefIcon() {
  return (
    <svg className="h-3.5 w-3.5" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={1.75}>
      <path strokeLinecap="round" strokeLinejoin="round"
        d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
    </svg>
  );
}

function ResearchIcon() {
  return (
    <svg className="h-3.5 w-3.5" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={1.75}>
      <path strokeLinecap="round" strokeLinejoin="round"
        d="M9.75 3.104v5.714a2.25 2.25 0 01-.659 1.591L5 14.5M9.75 3.104c-.251.023-.501.05-.75.082m.75-.082a24.301 24.301 0 014.5 0m0 0v5.714c0 .597.237 1.17.659 1.591L19.8 15.3M14.25 3.104c.251.023.501.05.75.082M19.8 15.3l-1.57.393A9.065 9.065 0 0112 15a9.065 9.065 0 00-6.23-.693L5 14.5m14.8.8l1.402 1.402c1 1 .03 2.798-1.442 2.798H6.24c-1.47 0-2.441-1.798-1.442-2.798L5 14.5" />
    </svg>
  );
}

function FilterIcon() {
  return (
    <svg className="h-3.5 w-3.5" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={1.75}>
      <path strokeLinecap="round" strokeLinejoin="round"
        d="M10.5 6h9.75M10.5 6a1.5 1.5 0 11-3 0m3 0a1.5 1.5 0 10-3 0M3.75 6H7.5m3 12h9.75m-9.75 0a1.5 1.5 0 01-3 0m3 0a1.5 1.5 0 00-3 0m-3.75 0H7.5m9-6h3.75m-3.75 0a1.5 1.5 0 01-3 0m3 0a1.5 1.5 0 00-3 0m-9.75 0h9.75" />
    </svg>
  );
}

function ArrowIcon() {
  return (
    <svg className="h-3.5 w-3.5" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2.5}>
      <path strokeLinecap="round" strokeLinejoin="round" d="M13 7l5 5m0 0l-5 5m5-5H6" />
    </svg>
  );
}
