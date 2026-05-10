import React, { useEffect, useState } from "react";

/**
 * AuthPanel — Phase 4 login widget.
 *
 * Fetches the list of demo orgs from GET /auth/orgs, lets the user
 * pick an org and enter a name, then calls POST /auth/token to get
 * a JWT.  The token is stored in component state and passed up via
 * onLogin(token, orgInfo).
 *
 * No passwords — this is a demo multi-tenant setup.
 */
export default function AuthPanel({ onLogin }) {
  const [orgs, setOrgs]         = useState([]);
  const [orgId, setOrgId]       = useState("");
  const [userId, setUserId]     = useState("");
  const [loading, setLoading]   = useState(false);
  const [error, setError]       = useState(null);
  const [loadingOrgs, setLoadingOrgs] = useState(true);

  useEffect(() => {
    fetch("/api/auth/orgs")
      .then((r) => r.json())
      .then((data) => {
        setOrgs(data);
        if (data.length) setOrgId(data[0].id);
      })
      .catch(() => setError("Could not load organisations"))
      .finally(() => setLoadingOrgs(false));
  }, []);

  async function handleLogin(e) {
    e.preventDefault();
    if (!orgId || !userId.trim()) return;
    setLoading(true);
    setError(null);

    try {
      const res = await fetch("/api/auth/token", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ org_id: orgId, user_id: userId.trim() }),
      });
      if (!res.ok) {
        const err = await res.json().catch(() => ({}));
        throw new Error(err.detail || `Login failed (${res.status})`);
      }
      const data = await res.json();
      onLogin(data.access_token, {
        orgId:   data.org_id,
        orgName: data.org_name,
        plan:    data.plan,
        userId:  userId.trim(),
      });
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  }

  const selectedOrg = orgs.find((o) => o.id === orgId);

  return (
    <div className="min-h-screen bg-background flex items-center justify-center px-4">
      <div className="w-full max-w-sm glass-panel rounded-2xl p-8 border border-white/10
        shadow-2xl shadow-cyan-900/10">

        {/* Logo */}
        <div className="text-center mb-8">
          <span className="text-3xl font-black tracking-tighter text-transparent bg-clip-text
            bg-gradient-to-r from-cyan-400 to-violet-500 font-headline select-none">
            ARIA
          </span>
          <p className="text-xs text-on-surface-variant mt-1 font-data">
            Account Research &amp; Intelligence Agent — Phase 4
          </p>
        </div>

        {/* Form */}
        <form onSubmit={handleLogin} className="flex flex-col gap-4">

          {/* Org selector */}
          <div>
            <label className="block text-xs font-bold text-on-surface-variant mb-1.5 uppercase tracking-wider font-data">
              Organisation
            </label>
            {loadingOrgs ? (
              <div className="h-10 rounded-lg bg-surface-container animate-pulse" />
            ) : (
              <select
                value={orgId}
                onChange={(e) => setOrgId(e.target.value)}
                className="w-full rounded-lg bg-surface-container border border-white/10
                  text-on-surface text-sm px-3 py-2.5 focus:outline-none
                  focus:border-secondary/50 focus:ring-1 focus:ring-secondary/30 transition"
              >
                {orgs.map((o) => (
                  <option key={o.id} value={o.id}>
                    {o.name} ({o.plan})
                  </option>
                ))}
              </select>
            )}
            {selectedOrg && (
              <p className="text-[10px] text-on-surface-variant mt-1 font-data">
                Plan: <span className="capitalize text-secondary">{selectedOrg.plan}</span>
              </p>
            )}
          </div>

          {/* User name */}
          <div>
            <label className="block text-xs font-bold text-on-surface-variant mb-1.5 uppercase tracking-wider font-data">
              Your name
            </label>
            <input
              type="text"
              value={userId}
              onChange={(e) => setUserId(e.target.value)}
              placeholder="e.g. alice"
              className="w-full rounded-lg bg-surface-container border border-white/10
                text-on-surface text-sm px-3 py-2.5 focus:outline-none
                focus:border-secondary/50 focus:ring-1 focus:ring-secondary/30 transition
                placeholder:text-slate-600"
              required
            />
          </div>

          {/* Error */}
          {error && (
            <p className="text-xs text-error bg-error/10 border border-error/20 rounded-lg px-3 py-2">
              {error}
            </p>
          )}

          {/* Submit */}
          <button
            type="submit"
            disabled={loading || !orgId || !userId.trim()}
            className="w-full py-2.5 rounded-lg bg-secondary text-on-secondary font-bold text-sm
              hover:bg-secondary/90 transition disabled:opacity-40 disabled:cursor-not-allowed
              focus:outline-none focus:ring-2 focus:ring-secondary/50"
          >
            {loading ? "Signing in…" : "Sign in"}
          </button>
        </form>

        {/* Footer hint */}
        <p className="text-[10px] text-slate-600 text-center mt-6 font-data leading-relaxed">
          Demo mode — no password required.<br />
          Select an org, enter any name, and sign in.
        </p>
      </div>
    </div>
  );
}
