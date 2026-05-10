import React, { useState } from "react";
import SearchForm, { WORKFLOW_STEPS } from "./components/SearchForm";
import BriefDisplay from "./components/BriefDisplay";
import ResearchDisplay from "./components/ResearchDisplay";
import AuthPanel from "./components/AuthPanel";
import CostDashboard from "./components/CostDashboard";
import { streamBrief, streamResearch, setAuthToken } from "./api/client";
import "./App.css";

// ── Agent step definitions ─────────────────────────────────────────────────

const RESEARCH_AGENTS = [
  { key: "planner",     label: "Planning workflow",        desc: "Goal analysis + routing"    },
  { key: "trial_agent", label: "Fetching trial data",      desc: "ClinicalTrials.gov v2"      },
  { key: "intel_agent", label: "Gathering intelligence",   desc: "Market signals + analysis"  },
  { key: "fit_scorer",  label: "Scoring CRO fit",          desc: "5 weighted dimensions"      },
  { key: "synthesizer", label: "Synthesising output",      desc: "Goal-driven freeform output" },
];

// ── Helper: summarise each agent's result into one readable line ───────────

// One-liner summary from raw agent_complete data (keys match SSE event structure)
function agentSummaryText(key, data) {
  if (!data) return "";
  switch (key) {
    case "planner":     return data.execution_plan?.output_format ? `Routing → ${data.execution_plan.output_format.replace(/_/g, " ")}` : "";
    case "trial_agent": return data.trial_data?.total_count !== undefined ? `${data.trial_data.total_count} active trials` : "";
    case "intel_agent": return `${data.intel_data?.key_signals?.length || 0} BD signals · ${data.intel_data?.pipeline_updates?.length || 0} pipeline updates`;
    case "fit_scorer":  return data.fit_score?.total_score !== undefined ? `Score: ${data.fit_score.total_score} / 100` : "";
    case "synthesizer": return "Output ready";
    default:            return "";
  }
}

// ── App ────────────────────────────────────────────────────────────────────

export default function App() {
  const [authToken, setAuthTokenState] = useState(null);
  const [orgInfo,   setOrgInfo]        = useState(null);
  const [showDash,  setShowDash]       = useState(false);
  const [mode,      setMode]           = useState("brief");

  // Brief state
  const [briefLoading, setBriefLoading] = useState(false);
  const [briefResult,  setBriefResult]  = useState(null);
  const [briefError,   setBriefError]   = useState(null);
  const [streamText,   setStreamText]   = useState("");
  const [briefStep,    setBriefStep]    = useState(0);

  // Research state
  const [researchLoading,  setResearchLoading]  = useState(false);
  const [researchResult,   setResearchResult]   = useState(null);
  const [researchError,    setResearchError]    = useState(null);
  const [completedAgents,  setCompletedAgents]  = useState([]);
  const [currentAgent,     setCurrentAgent]     = useState(null);
  const [researchFilters,  setResearchFilters]  = useState({});
  const [agentData,        setAgentData]        = useState({});
  const [skippedAgents,    setSkippedAgents]    = useState([]);

  function handleLogin(token, info) {
    setAuthToken(token);
    setAuthTokenState(token);
    setOrgInfo(info);
  }

  function handleLogout() {
    setAuthToken(null);
    setAuthTokenState(null);
    setOrgInfo(null);
    setShowDash(false);
  }

  if (!authToken) return <AuthPanel onLogin={handleLogin} />;

  async function handleBriefSearch(companyName) {
    setResearchResult(null); setResearchError(null); setResearchLoading(false);
    setBriefLoading(true); setBriefError(null); setBriefResult(null); setStreamText(""); setBriefStep(1);
    await streamBrief(companyName, {
      onStatus: (msg) => setBriefStep(msg.toLowerCase().includes("generating") ? 2 : 1),
      onChunk:  (text) => setStreamText((prev) => prev + text),
      onDone:   (data) => { setBriefResult(data); setBriefStep(3); setBriefLoading(false); setStreamText(""); },
      onError:  (msg)  => { setBriefError(msg);   setBriefStep(0); setBriefLoading(false); setStreamText(""); },
    });
  }

  async function handleResearchSearch(companyName, goal, filters, previousContext = null) {
    setBriefResult(null); setBriefError(null); setBriefLoading(false); setStreamText(""); setBriefStep(0);
    setResearchLoading(true); setResearchError(null); setResearchResult(null);
    setCompletedAgents([]); setCurrentAgent(RESEARCH_AGENTS[0].key);

    // Pre-compute which agents will self-skip because data is already cached.
    // Store in the same shape as the SSE agent_complete data payload so that
    // the detail components use identical access paths regardless of source.
    const skipped = [];
    const initData = {};
    if (previousContext?.trial_data?.total_count !== undefined) {
      skipped.push("trial_agent");
      initData["trial_agent"] = { trial_data: previousContext.trial_data };
    }
    if (previousContext?.intel_data?.key_signals?.length) {
      skipped.push("intel_agent");
      initData["intel_agent"] = { intel_data: previousContext.intel_data };
    }
    if (previousContext?.fit_score?.total_score !== undefined) {
      skipped.push("fit_scorer");
      initData["fit_scorer"] = { fit_score: previousContext.fit_score };
    }
    setSkippedAgents(skipped);
    setAgentData(initData);

    await streamResearch(companyName, goal, filters, {
      onAgentComplete: (agent, data) => {
        setCompletedAgents((prev) => [...prev, agent]);
        setAgentData((prev) => ({ ...prev, [agent]: data }));
        // Advance currentAgent, jumping over any cached agents
        const curIdx = RESEARCH_AGENTS.findIndex((a) => a.key === agent);
        let nextIdx = curIdx + 1;
        while (nextIdx < RESEARCH_AGENTS.length && skipped.includes(RESEARCH_AGENTS[nextIdx].key)) nextIdx++;
        setCurrentAgent(nextIdx < RESEARCH_AGENTS.length ? RESEARCH_AGENTS[nextIdx].key : null);
      },
      onDone:  (result) => { setResearchResult(result); setResearchLoading(false); setCurrentAgent(null); },
      onError: (msg)    => { setResearchError(msg);     setResearchLoading(false); setCurrentAgent(null); },
    }, previousContext);
  }

  function handleSearch(companyName, goal, filters, previousContext = null) {
    if (goal) { setMode("research"); handleResearchSearch(companyName, goal, filters, previousContext); }
    else       { setMode("brief");   handleBriefSearch(companyName); }
  }

  function handleReset() {
    setMode("brief");
    setBriefLoading(false); setBriefResult(null); setBriefError(null); setStreamText(""); setBriefStep(0);
    setResearchLoading(false); setResearchResult(null); setResearchError(null);
    setCompletedAgents([]); setCurrentAgent(null); setResearchFilters({});
    setAgentData({}); setSkippedAgents([]);
  }

  const loading = mode === "brief" ? briefLoading  : researchLoading;
  const result  = mode === "brief" ? briefResult   : researchResult;
  const error   = mode === "brief" ? briefError    : researchError;

  // Next-step derivations
  const lastCompany = mode === "brief" ? result?.brief?.company_name : result?.company_name;
  const currentFormat = mode === "brief" ? "brief" : (result?.execution_plan?.output_format ?? null);
  const currentStepIndex = currentFormat === "brief" ? -1 : WORKFLOW_STEPS.findIndex((s) => s.format === currentFormat);
  const nextStep = result && currentStepIndex < WORKFLOW_STEPS.length - 1 ? WORKFLOW_STEPS[currentStepIndex + 1] : null;

  return (
    <div className="h-screen flex flex-col bg-background text-on-surface overflow-hidden">

      {/* ── Top bar ─────────────────────────────────────────────────────── */}
      <header className="flex-shrink-0 z-50 w-full flex items-center justify-between px-5 py-2.5
        bg-surface-container-lowest/90 backdrop-blur-xl border-b border-white/8">

        {/* Brand — visible on all sizes */}
        <div className="flex items-center gap-3">
          <span className="text-xl font-black tracking-tighter text-transparent bg-clip-text
            bg-gradient-to-r from-[#009afe] to-[#ba7ce3] font-headline select-none">
            ARIA
          </span>
          <span className="hidden sm:block text-[10px] font-data uppercase tracking-[0.18em]
            text-on-surface-variant/50 border-l border-white/10 pl-3">
            CRO Intelligence Hub
          </span>
        </div>

        {/* Status + user controls */}
        <div className="flex items-center gap-3">
          <span className="h-1.5 w-1.5 rounded-full bg-tertiary animate-pulse flex-shrink-0" />
          <span className="text-[11px] text-tertiary font-data hidden sm:block">System operational</span>

          {orgInfo && (
            <span className="hidden md:block text-[10px] bg-surface-container border border-white/8
              text-on-surface-variant font-data px-2 py-1 rounded">
              {orgInfo.orgName} · {orgInfo.userId}
            </span>
          )}
        </div>
      </header>

      {/* Cost dashboard overlay */}
      {showDash && (
        <CostDashboard token={authToken} orgInfo={orgInfo} onClose={() => setShowDash(false)} />
      )}

      {/* ── Body: sidebar + main ─────────────────────────────────────────── */}
      <div className="flex flex-1 min-h-0 overflow-hidden">

        {/* ── Sidebar ── */}
        <aside className="hidden lg:flex flex-col w-60 flex-shrink-0
          bg-surface-container-lowest border-r border-white/8">

          {/* Nav section label */}
          <div className="px-5 pt-6 pb-4">
            <p className="text-[10px] font-data uppercase tracking-[0.22em] text-on-surface-variant/40">
              Navigation
            </p>
          </div>

          {/* Nav items */}
          <nav className="flex-1 space-y-0.5 px-2">
            {/* Research — always active (our single tool) */}
            <div className="nav-active flex items-center gap-3 px-4 py-3 rounded cursor-default select-none">
              <ResearchNavIcon className="h-4 w-4 text-primary-container flex-shrink-0" />
              <div className="min-w-0">
                <p className="text-xs font-data font-bold uppercase tracking-wider text-primary">
                  Research Agent
                </p>
                <p className="text-[10px] text-on-surface-variant/50 font-data mt-0.5 truncate">
                  Trials · Intel · Fit · Synthesis
                </p>
              </div>
            </div>

            {/* Usage dashboard */}
            <button
              onClick={() => setShowDash(true)}
              className="w-full flex items-center gap-3 px-4 py-3 rounded text-left
                text-on-surface-variant/60 hover:text-on-surface hover:bg-white/5
                transition-all duration-150 group"
            >
              <UsageNavIcon className="h-4 w-4 flex-shrink-0 group-hover:text-secondary" />
              <p className="text-xs font-data uppercase tracking-wider">Usage</p>
            </button>
          </nav>

          {/* Bottom: org info + sign out */}
          <div className="px-5 py-5 border-t border-white/8 space-y-3">
            {orgInfo && (
              <div className="text-[10px] font-data text-on-surface-variant/50 truncate">
                {orgInfo.orgName} · {orgInfo.userId}
              </div>
            )}
            <button
              onClick={handleLogout}
              className="flex items-center gap-2 text-[11px] font-data text-on-surface-variant/50
                hover:text-on-surface transition-colors"
            >
              <SignOutIcon className="h-3.5 w-3.5" />
              Sign out
            </button>
          </div>
        </aside>

        {/* ── Main content ── */}
        <div className="flex-1 min-h-0 overflow-y-auto relative">
          <main className={`w-full px-6 py-8 ${result || loading ? "pb-24" : ""}`}>

            {!result && !loading && <HeroSection />}

            {!result && !loading && (
              <div className="max-w-2xl mx-auto mb-8">
                <SearchForm
                  onSearch={handleSearch}
                  loading={loading}
                  filters={researchFilters}
                  onFiltersChange={setResearchFilters}
                />
              </div>
            )}

            {/* Brief loading */}
            {mode === "brief" && briefLoading && (
              <div className="glass-panel rounded-lg p-6 mb-6 animate-fade-in">
                <BriefSteps step={briefStep} />
                {streamText && (
                  <div className="mt-5 pt-5 border-t border-white/8">
                    <p className="text-[10px] font-bold text-tertiary uppercase tracking-widest mb-3 font-data">
                      Claude is writing…
                    </p>
                    <pre className="text-xs text-on-surface-variant font-mono whitespace-pre-wrap
                      max-h-44 overflow-y-auto leading-relaxed">
                      {streamText}
                    </pre>
                  </div>
                )}
              </div>
            )}

            {/* Research loading */}
            {mode === "research" && researchLoading && (
              <div className="glass-panel rounded-lg p-6 mb-6 animate-fade-in">
                <ResearchSteps
                  completed={completedAgents}
                  current={currentAgent}
                  skippedAgents={skippedAgents}
                  agentData={agentData}
                />
              </div>
            )}

            {/* Error */}
            {error && (
              <div className="glass-panel rounded-lg p-4 mb-6 flex items-start gap-3
                border-l-4 border-error animate-fade-in">
                <svg className="h-5 w-5 text-error flex-shrink-0 mt-0.5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2}
                    d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-2.5L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16.5c-.77.833.192 2.5 1.732 2.5z" />
                </svg>
                <div>
                  <p className="text-sm font-bold text-error">Something went wrong</p>
                  <p className="text-sm text-on-surface-variant mt-0.5">{error}</p>
                </div>
              </div>
            )}

            {/* Results */}
            {result && (
              <div className="animate-fade-in">
                {mode === "brief"    && <BriefDisplay    data={result} />}
                {mode === "research" && <ResearchDisplay data={result} />}
              </div>
            )}
          </main>

          {/* ── Sticky bottom bar (offset for sidebar on lg+) ── */}
          {(result || loading) && (
            <div className="fixed bottom-0 left-0 lg:left-60 right-0 z-40
              border-t border-white/8 bg-surface-container-lowest/95 backdrop-blur-xl
              px-6 py-3 animate-fade-in">
              <div className="w-full flex items-center gap-3">

                {/* New Search — resets all state, returns to home */}
                <button
                  type="button"
                  onClick={handleReset}
                  disabled={loading}
                  className="flex-shrink-0 flex items-center gap-1.5 px-3 py-1.5 rounded-lg
                    text-xs font-medium border border-white/10 bg-surface-container
                    text-on-surface-variant hover:text-on-surface hover:border-white/20
                    disabled:opacity-40 transition-all duration-150"
                >
                  <svg className="h-3.5 w-3.5" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
                    <path strokeLinecap="round" strokeLinejoin="round" d="M21 21l-4.35-4.35M17 11A6 6 0 115 11a6 6 0 0112 0z" />
                  </svg>
                  New Search
                </button>

                {/* Next-step prompt — fills remaining space */}
                {nextStep && lastCompany && !loading && (
                  <div className="flex-1 flex items-center justify-between gap-3
                    px-3.5 py-2 rounded-xl border bg-surface-container border-secondary/15
                    text-xs text-on-surface-variant">
                    <div className="flex items-center gap-2.5 min-w-0">
                      <span className="flex-shrink-0 h-5 w-5 rounded-full bg-secondary/15 border border-secondary/25
                        text-[10px] font-bold font-data text-secondary flex items-center justify-center">
                        {nextStep.step}
                      </span>
                      <span className="truncate">
                        Next:{" "}
                        <span className="text-on-surface font-medium">{nextStep.label}</span>
                        {" "}for{" "}
                        <span className="text-secondary font-medium">{lastCompany}</span>
                      </span>
                    </div>
                    <button
                      type="button"
                      onClick={() => handleSearch(lastCompany, nextStep.value, {}, result)}
                      className="flex-shrink-0 flex items-center gap-1.5 px-3 py-1 rounded-lg
                        text-xs font-bold bg-gradient-to-tl from-secondary-container to-secondary
                        text-white shadow shadow-secondary/20
                        hover:opacity-90 active:scale-[0.97] transition-all duration-150"
                    >
                      Run
                      <svg className="h-3 w-3" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2.5}>
                        <path strokeLinecap="round" strokeLinejoin="round" d="M13 7l5 5m0 0l-5 5m5-5H6" />
                      </svg>
                    </button>
                  </div>
                )}

              </div>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}

// ── Hero section ───────────────────────────────────────────────────────────

const HERO_OUTPUTS = [
  { label: "BD Outreach Email",  detail: "RAG-grounded, personalised",    time: "~60–90s" },
  { label: "Pipeline Summary",   detail: "Trial data + CRO opportunities", time: "~30–60s" },
  { label: "Competitive Brief",  detail: "Landscape + positioning",        time: "~30–60s" },
  { label: "Account Snapshot",   detail: "Quick exec read",                time: "~30s"    },
  { label: "Company Brief",      detail: "Trials + SEC filings",           time: "~15–30s" },
];

function HeroSection() {
  return (
    <div className="py-10 text-center animate-fade-in">
      <div className="inline-flex items-center gap-2 text-xs font-medium text-secondary
        bg-secondary/10 border border-secondary/20 px-3 py-1.5 rounded-full mb-6">
        <span className="h-1.5 w-1.5 rounded-full bg-tertiary animate-pulse" />
        AI-powered CRO Business Development Intelligence
      </div>

      <h1 className="text-4xl font-black tracking-tight font-headline mb-4">
        Know your next sponsor{" "}
        <span className="text-transparent bg-clip-text bg-gradient-to-r from-[#009afe] to-[#ba7ce3]">
          before you call.
        </span>
      </h1>

      <p className="text-on-surface-variant max-w-xl mx-auto leading-relaxed text-base mb-8">
        Enter a company name. Describe your goal — or leave it blank for a quick brief.
        ARIA routes the right agents and delivers exactly what you need.
      </p>

      <div className="flex flex-wrap justify-center gap-2">
        {HERO_OUTPUTS.map(({ label, detail, time }) => (
          <div key={label}
            className="flex flex-col items-start px-4 py-2.5 rounded-lg border
              bg-surface-container/50 border-white/8 text-left min-w-[140px]
              hover:border-primary/20 transition-colors duration-150">
            <span className="text-xs font-medium text-on-surface">{label}</span>
            <span className="text-[10px] text-on-surface-variant/60 mt-0.5">{detail}</span>
            <span className="text-[10px] text-tertiary/70 font-data mt-1">{time}</span>
          </div>
        ))}
      </div>
    </div>
  );
}

// ── Brief step indicator ───────────────────────────────────────────────────

const BRIEF_STEPS = [
  { id: 1, label: "Fetching ClinicalTrials.gov & SEC EDGAR" },
  { id: 2, label: "Generating brief with Claude" },
];

function BriefSteps({ step }) {
  return (
    <div className="flex items-center gap-6">
      {BRIEF_STEPS.map((s, idx) => {
        const done   = step > s.id;
        const active = step === s.id;
        return (
          <React.Fragment key={s.id}>
            <div className="flex items-center gap-2.5">
              <div className={`h-6 w-6 rounded-full flex items-center justify-center flex-shrink-0 text-xs font-bold transition-all
                ${done   ? "bg-tertiary"                                                            : ""}
                ${active ? "bg-tertiary/20 border-2 border-tertiary"                               : ""}
                ${!done && !active ? "bg-surface-container-high border-2 border-outline-variant"   : ""}
              `}>
                {done
                  ? <svg className="h-3 w-3 text-on-tertiary" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={3}><path strokeLinecap="round" strokeLinejoin="round" d="M5 13l4 4L19 7" /></svg>
                  : active
                    ? <span className="h-2 w-2 rounded-full bg-tertiary animate-pulse block" />
                    : <span className="text-on-surface-variant/40">{s.id}</span>
                }
              </div>
              <span className={`text-sm font-data
                ${active ? "text-on-surface font-medium" : done ? "text-on-surface-variant/50 line-through" : "text-on-surface-variant/40"}`}>
                {s.label}
              </span>
            </div>
            {idx < BRIEF_STEPS.length - 1 && (
              <div className={`flex-1 h-px ${step > s.id ? "bg-tertiary/30" : "bg-white/8"}`} />
            )}
          </React.Fragment>
        );
      })}
    </div>
  );
}

// ── Research step indicator ────────────────────────────────────────────────

function ResearchSteps({ completed, current, skippedAgents = [], agentData = {} }) {
  const [expanded, setExpanded] = useState({});

  // Auto-expand each step as it completes so results appear inline
  const prevCompletedRef = React.useRef([]);
  React.useEffect(() => {
    const newlyDone = completed.filter(k => !prevCompletedRef.current.includes(k));
    if (newlyDone.length) {
      setExpanded(prev => {
        const next = { ...prev };
        newlyDone.forEach(k => { next[k] = true; });
        return next;
      });
    }
    prevCompletedRef.current = completed;
  }, [completed]);

  return (
    <div className="flex flex-col gap-4">
      <p className="text-[10px] font-bold text-primary uppercase tracking-widest font-data">
        Running ARIA research workflow…
      </p>
      <div className="relative pl-8">
        <div className="absolute left-2.5 top-2 bottom-2 thought-line" />
        <div className="space-y-2">
          {RESEARCH_AGENTS.map((agent) => {
            const done    = completed.includes(agent.key);
            const cached  = skippedAgents.includes(agent.key);
            const active  = current === agent.key && !cached;
            const data    = agentData[agent.key];
            const isOpen  = expanded[agent.key] ?? false;
            const canOpen = (done || cached) && !!data;
            const oneLiner = data ? agentSummaryText(agent.key, data) : null;

            return (
              <div key={agent.key} className="relative">
                {/* Timeline dot */}
                <div className={`absolute -left-[26px] top-[18px] w-3 h-3 rounded-full transition-all duration-300
                  ${cached  ? "bg-secondary ring-4 ring-secondary/20"                                       : ""}
                  ${done    ? "bg-tertiary  ring-4 ring-tertiary/20"                                        : ""}
                  ${active  ? "bg-primary-container animate-pulse shadow-[0_0_8px_rgba(0,154,254,0.55)]"   : ""}
                  ${!done && !cached && !active ? "bg-surface-container-high border border-outline-variant" : ""}
                `} />

                {/* Card */}
                <div className={`rounded-lg border overflow-hidden transition-all duration-300
                  ${cached  ? "bg-surface-container      border-secondary/20"              : ""}
                  ${done    ? "bg-surface-container      border-tertiary/20"               : ""}
                  ${active  ? "bg-surface-container-high border-primary/20 primary-glow"  : ""}
                  ${!done && !cached && !active ? "bg-surface-container-low/50 border-white/5 opacity-40" : ""}
                `}>

                  {/* ── Header row (clickable when data exists) ── */}
                  <button
                    type="button"
                    disabled={!canOpen}
                    onClick={() => canOpen && setExpanded(p => ({ ...p, [agent.key]: !p[agent.key] }))}
                    className="w-full flex items-center gap-2 px-3 py-2.5 text-left"
                  >
                    <div className="flex-1 min-w-0">
                      <div className="flex items-center gap-2">
                        <p className={`text-sm font-medium leading-snug
                          ${done || cached || active ? "text-on-surface" : "text-on-surface-variant/40"}`}>
                          {agent.label}
                        </p>
                        {/* Animated dots while active */}
                        {active && (
                          <span className="flex gap-0.5">
                            {[0, 1, 2].map(i => (
                              <span key={i} className="h-1 w-1 rounded-full bg-primary animate-bounce"
                                style={{ animationDelay: `${i * 150}ms` }} />
                            ))}
                          </span>
                        )}
                      </div>
                      <p className="text-[10px] text-on-surface-variant/45 font-data">{agent.desc}</p>
                      {oneLiner && (done || cached) && (
                        <p className={`text-[10px] font-data mt-0.5 ${cached ? "text-secondary/70" : "text-tertiary/70"}`}>
                          {oneLiner}{cached ? " · cached" : ""}
                        </p>
                      )}
                    </div>

                    <div className="flex items-center gap-1.5 flex-shrink-0">
                      <span className={`text-[10px] font-bold uppercase tracking-wider font-data
                        ${cached ? "text-secondary"               : ""}
                        ${done   ? "text-tertiary"                : ""}
                        ${active ? "text-primary"                 : ""}
                        ${!done && !cached && !active ? "text-on-surface-variant/25" : ""}
                      `}>
                        {cached ? "CACHED" : done ? "DONE" : active ? "ACTIVE" : "QUEUED"}
                      </span>
                      {canOpen && (
                        <svg className={`h-3 w-3 text-on-surface-variant/35 transition-transform duration-200
                          ${isOpen ? "rotate-180" : ""}`}
                          fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2.5}>
                          <path strokeLinecap="round" strokeLinejoin="round" d="M19 9l-7 7-7-7" />
                        </svg>
                      )}
                    </div>
                  </button>

                  {/* ── Expandable detail panel ── */}
                  {isOpen && data && (
                    <div className="px-3 pb-3 border-t border-white/8">
                      <AgentStepDetail agentKey={agent.key} data={data} />
                    </div>
                  )}
                </div>
              </div>
            );
          })}
        </div>
      </div>
    </div>
  );
}

// ── Per-agent detail panels ────────────────────────────────────────────────

function AgentStepDetail({ agentKey, data }) {
  switch (agentKey) {
    case "planner":     return <PlannerDetail     plan={data.execution_plan} />;
    case "trial_agent": return <TrialDetail       trial={data.trial_data} />;
    case "intel_agent": return <IntelDetail       intel={data.intel_data} />;
    case "fit_scorer":  return <FitDetail         fit={data.fit_score} />;
    case "synthesizer": return <SynthesizerDetail />;
    default:            return null;
  }
}

function PlannerDetail({ plan }) {
  if (!plan) return null;
  return (
    <div className="pt-2.5 flex flex-col gap-2">
      <div className="flex flex-wrap items-center gap-2">
        {plan.output_format && (
          <span className="text-[10px] px-2 py-0.5 rounded-full bg-primary/10 text-primary border border-primary/20 font-data font-bold">
            {plan.output_format.replace(/_/g, " ")}
          </span>
        )}
        {plan.agents?.map(a => (
          <span key={a} className="text-[10px] px-2 py-0.5 rounded-full bg-secondary/10 text-secondary/80 border border-secondary/15 font-data">
            {a.replace(/_/g, " ")}
          </span>
        ))}
      </div>
      {plan.rationale && (
        <p className="text-[10px] text-on-surface-variant/60 font-data italic leading-relaxed border-t border-white/8 pt-2">
          {plan.rationale}
        </p>
      )}
    </div>
  );
}

function TrialDetail({ trial }) {
  if (!trial) return null;
  const phases = Object.entries(trial.phases || {}).sort((a, b) => b[1] - a[1]);
  const total  = trial.total_count || 0;
  return (
    <div className="pt-2.5 flex flex-col gap-2">
      <div className="flex items-baseline gap-1.5">
        <span className="text-lg font-bold font-data text-on-surface">{total}</span>
        <span className="text-[10px] text-on-surface-variant/50 font-data">active trials</span>
      </div>
      {phases.length > 0 && (
        <div className="flex flex-col gap-1">
          {phases.map(([phase, count]) => (
            <div key={phase} className="flex items-center gap-2">
              <span className="text-[10px] font-data text-on-surface-variant/55 w-20 flex-shrink-0 truncate">
                {phase.replace("EARLY_PHASE", "Early Ph.").replace("PHASE", "Phase ")}
              </span>
              <div className="flex-1 h-1 bg-surface-container-highest rounded-full overflow-hidden">
                <div className="h-full bg-secondary/55 rounded-full transition-all"
                  style={{ width: total > 0 ? `${(count / total) * 100}%` : "0%" }} />
              </div>
              <span className="text-[10px] font-bold font-data text-secondary tabular-nums w-4 text-right">{count}</span>
            </div>
          ))}
        </div>
      )}
      {trial.conditions?.slice(0, 3).length > 0 && (
        <p className="text-[10px] text-on-surface-variant/45 font-data border-t border-white/8 pt-2 leading-relaxed">
          {trial.conditions.slice(0, 3).join(" · ")}
        </p>
      )}
    </div>
  );
}

function IntelDetail({ intel }) {
  if (!intel) return null;
  const signals = intel.key_signals || [];
  const updates = intel.pipeline_updates || [];
  const cro     = intel.cro_partnership_indicators || [];
  return (
    <div className="pt-2.5 flex flex-col gap-1.5">
      {signals.slice(0, 2).map((s, i) => (
        <div key={i} className="flex gap-1.5">
          <span className="text-secondary/60 text-[10px] flex-shrink-0 mt-px">·</span>
          <p className="text-[10px] text-on-surface-variant/65 font-data leading-relaxed">{s}</p>
        </div>
      ))}
      {signals.length > 2 && (
        <p className="text-[10px] text-on-surface-variant/35 font-data pl-3">+{signals.length - 2} more signals</p>
      )}
      <div className="flex gap-3 pt-1.5 border-t border-white/8 mt-0.5">
        <span className="text-[10px] font-data text-on-surface-variant/45">{updates.length} pipeline updates</span>
        <span className="text-[10px] font-data text-on-surface-variant/45">{cro.length} CRO indicators</span>
      </div>
    </div>
  );
}

function FitDetail({ fit }) {
  if (!fit) return null;
  return (
    <div className="pt-2.5 flex flex-col gap-2">
      <div className="flex items-baseline gap-1.5">
        <span className="text-2xl font-bold font-data text-secondary">{fit.total_score}</span>
        <span className="text-[10px] text-on-surface-variant/50 font-data">/ 100</span>
      </div>
      {fit.summary && (
        <p className="text-[10px] text-on-surface-variant/65 font-data leading-relaxed">{fit.summary}</p>
      )}
    </div>
  );
}

function SynthesizerDetail() {
  return (
    <p className="pt-2.5 text-[10px] text-on-surface-variant/45 font-data">
      Output synthesised — see results below ↓
    </p>
  );
}

// ── Sidebar icons ──────────────────────────────────────────────────────────

function ResearchNavIcon({ className }) {
  return (
    <svg className={className} fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={1.75}>
      <path strokeLinecap="round" strokeLinejoin="round"
        d="M9.75 3.104v5.714a2.25 2.25 0 01-.659 1.591L5 14.5M9.75 3.104c-.251.023-.501.05-.75.082m.75-.082a24.301 24.301 0 014.5 0m0 0v5.714c0 .597.237 1.17.659 1.591L19.8 15.3M14.25 3.104c.251.023.501.05.75.082M19.8 15.3l-1.57.393A9.065 9.065 0 0112 15a9.065 9.065 0 00-6.23-.693L5 14.5m14.8.8l1.402 1.402c1 1 .03 2.798-1.442 2.798H6.24c-1.47 0-2.441-1.798-1.442-2.798L5 14.5" />
    </svg>
  );
}

function UsageNavIcon({ className }) {
  return (
    <svg className={className} fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={1.75}>
      <path strokeLinecap="round" strokeLinejoin="round"
        d="M3 13.125C3 12.504 3.504 12 4.125 12h2.25c.621 0 1.125.504 1.125 1.125v6.75C7.5 20.496 6.996 21 6.375 21h-2.25A1.125 1.125 0 013 19.875v-6.75zM9.75 8.625c0-.621.504-1.125 1.125-1.125h2.25c.621 0 1.125.504 1.125 1.125v11.25c0 .621-.504 1.125-1.125 1.125h-2.25a1.125 1.125 0 01-1.125-1.125V8.625zM16.5 4.125c0-.621.504-1.125 1.125-1.125h2.25C20.496 3 21 3.504 21 4.125v15.75c0 .621-.504 1.125-1.125 1.125h-2.25a1.125 1.125 0 01-1.125-1.125V4.125z" />
    </svg>
  );
}

function SignOutIcon({ className }) {
  return (
    <svg className={className} fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={1.75}>
      <path strokeLinecap="round" strokeLinejoin="round"
        d="M15.75 9V5.25A2.25 2.25 0 0013.5 3h-6a2.25 2.25 0 00-2.25 2.25v13.5A2.25 2.25 0 007.5 21h6a2.25 2.25 0 002.25-2.25V15M12 9l-3 3m0 0l3 3m-3-3h12.75" />
    </svg>
  );
}
