/**
 * DietSense — SafetyShield
 * Phase 8B: Real-time dietary safety audit dashboard.
 * Reads actual user dietary preferences and allergens from the backend.
 * Logic sourced exclusively from ml.scoring.safety_gate — Gemini is never
 * involved in safety decisions.
 */

"use client";

import React, { useEffect, useState, useCallback } from "react";
import { apiClient } from "@/lib/api-client";
import { useAuth } from "@/context/AuthContext";

// ─── Types ───────────────────────────────────────────────────────────────────

interface ActiveRule {
  rule: string;
  label: string;
  value: string;
}

interface BlockedCandidate {
  item: {
    id: number | null;
    name: string;
    calories: number | null;
    tags: string[];
    allergens: string[];
  };
  reason: string;
  rule: string;
  conflict: string;
}

interface SafetyShieldData {
  active_rules: ActiveRule[];
  safe_count: number;
  blocked_count: number;
  total_audited: number;
  blocked_candidates: BlockedCandidate[];
}

// ─── Helpers ─────────────────────────────────────────────────────────────────

function ruleIcon(rule: string): string {
  if (rule === "allergen" || rule === "allergen_conflict" || rule === "allergen_unknown") return "🧪";
  if (rule === "diet" || rule === "vegetarian" || rule === "vegan" || rule === "eggetarian" || rule === "pescatarian") return "🌿";
  return "🛡️";
}

function conflictBadge(rule: string) {
  if (rule.includes("allergen")) return "bg-red-50 text-red-700 border-red-200";
  if (rule === "vegan") return "bg-emerald-50 text-emerald-700 border-emerald-200";
  return "bg-amber-50 text-amber-700 border-amber-200";
}

// ─── Component ───────────────────────────────────────────────────────────────

export const SafetyShield: React.FC = () => {
  const { isAuthenticated } = useAuth();
  const [data, setData] = useState<SafetyShieldData | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [showAll, setShowAll] = useState(false);

  const fetchShield = useCallback(async () => {
    if (!isAuthenticated) return;
    setLoading(true);
    setError(null);
    try {
      const result = await apiClient<SafetyShieldData>("/api/recommendations/safety-shield", {
        method: "GET",
      });
      setData(result);
    } catch (err: any) {
      setError(err?.message || "Failed to load safety shield data");
    } finally {
      setLoading(false);
    }
  }, [isAuthenticated]);

  useEffect(() => {
    fetchShield();
  }, [fetchShield]);

  // ─── Not authenticated ──────────────────────────────────────────────────
  if (!isAuthenticated) {
    return (
      <div className="relative z-10 space-y-4">
        <div className="rounded-2xl bg-white p-6 border border-[#e8ded3] text-center shadow-sm">
          <span className="text-3xl">🔒</span>
          <h3 className="text-base font-serif text-[#421018] mt-3">Sign in to view your Safety Shield</h3>
          <p className="text-xs text-slate-500 mt-1">Your dietary restrictions and allergen exclusion gates are protected by your account.</p>
        </div>
      </div>
    );
  }

  // ─── Loading ────────────────────────────────────────────────────────────
  if (loading) {
    return (
      <div className="relative z-10 space-y-4">
        <div className="rounded-2xl bg-white p-6 border border-[#e8ded3] shadow-sm flex items-center gap-3">
          <span className="material-symbols-outlined animate-spin text-[#581825]">refresh</span>
          <p className="text-sm text-slate-500">Auditing food catalog against your safety profile…</p>
        </div>
      </div>
    );
  }

  // ─── Error ──────────────────────────────────────────────────────────────
  if (error) {
    return (
      <div className="relative z-10 space-y-4">
        <div className="rounded-2xl bg-white p-5 border border-red-200 shadow-sm">
          <p className="text-sm text-red-700">⚠️ {error}</p>
          <button
            onClick={fetchShield}
            className="mt-3 px-4 py-2 text-xs bg-[#581825] text-white rounded-lg hover:bg-[#421018] transition"
          >
            Retry
          </button>
        </div>
      </div>
    );
  }

  // ─── No data yet ────────────────────────────────────────────────────────
  if (!data) return null;

  const displayedBlocked = showAll ? data.blocked_candidates : data.blocked_candidates.slice(0, 6);
  const safePercent = data.total_audited > 0
    ? Math.round((data.safe_count / data.total_audited) * 100)
    : 100;

  return (
    <div className="relative z-10 space-y-4">
      {/* ── Header Stats ── */}
      <div className="grid grid-cols-3 gap-3">
        <div className="rounded-2xl bg-white p-4 border border-[#e8ded3] shadow-sm text-center">
          <div className="text-2xl font-bold text-emerald-600">{data.safe_count}</div>
          <div className="text-[11px] text-slate-500 mt-0.5">Safe Foods</div>
        </div>
        <div className="rounded-2xl bg-white p-4 border border-[#e8ded3] shadow-sm text-center">
          <div className="text-2xl font-bold text-red-600">{data.blocked_count}</div>
          <div className="text-[11px] text-slate-500 mt-0.5">Blocked</div>
        </div>
        <div className="rounded-2xl bg-white p-4 border border-[#e8ded3] shadow-sm text-center">
          <div className="text-2xl font-bold text-[#421018]">{safePercent}%</div>
          <div className="text-[11px] text-slate-500 mt-0.5">Safe Rate</div>
        </div>
      </div>

      {/* ── Active Safety Rules ── */}
      <div className="rounded-2xl bg-white p-5 border border-[#e8ded3] border-l-4 border-l-[#581825] shadow-sm">
        <h4 className="text-sm font-serif text-[#421018] flex items-center gap-2 mb-3">
          <span>🚫</span> Active Safety Rules
        </h4>
        <div className="flex flex-wrap gap-2">
          {data.active_rules.map((rule, idx) => (
            <span
              key={idx}
              className={`px-2.5 py-1 rounded-lg text-xs font-medium border ${
                rule.rule === "allergen"
                  ? "bg-red-50 text-red-700 border-red-200"
                  : rule.rule === "diet"
                  ? "bg-blue-50 text-blue-700 border-blue-200"
                  : "bg-slate-50 text-slate-600 border-slate-200"
              }`}
              title={rule.label}
            >
              {ruleIcon(rule.rule)} {rule.label}
            </span>
          ))}
        </div>
        <p className="text-[11px] text-slate-400 mt-3">
          Audited {data.total_audited} foods from catalog. Safety logic runs in
          <span className="font-semibold"> ml.scoring.safety_gate</span> — never bypassed by AI.
        </p>
      </div>

      {/* ── Blocked Candidates ── */}
      {data.blocked_candidates.length > 0 && (
        <div className="rounded-2xl bg-white p-5 border border-[#e8ded3] shadow-sm">
          <h4 className="text-sm font-serif text-[#421018] mb-3">
            🛑 Blocked from Your Plan ({data.blocked_count})
          </h4>
          <div className="space-y-2">
            {displayedBlocked.map((b, idx) => (
              <div
                key={idx}
                className={`flex items-start justify-between gap-3 p-3 rounded-xl border ${conflictBadge(b.rule)}`}
              >
                <div className="flex-1 min-w-0">
                  <p className="text-sm font-medium truncate">{b.item.name || "Unknown food"}</p>
                  <p className="text-[11px] opacity-80 mt-0.5">{b.reason}</p>
                </div>
                <span className="shrink-0 px-2 py-0.5 rounded-full text-[10px] font-bold bg-white/60 border border-current">
                  {b.rule.replace(/_/g, " ").toUpperCase()}
                </span>
              </div>
            ))}
          </div>

          {data.blocked_candidates.length > 6 && (
            <button
              onClick={() => setShowAll((v) => !v)}
              className="mt-3 w-full text-xs text-[#581825] font-medium underline-offset-2 hover:underline"
            >
              {showAll ? "Show fewer" : `Show all ${data.blocked_candidates.length} blocked foods`}
            </button>
          )}
        </div>
      )}

      {/* ── Empty blocked ── */}
      {data.blocked_candidates.length === 0 && (
        <div className="rounded-2xl bg-white p-5 border border-emerald-200 shadow-sm text-center">
          <span className="text-3xl">✅</span>
          <p className="text-sm text-emerald-700 font-medium mt-2">All audited foods are safe for your profile</p>
          <p className="text-xs text-slate-400 mt-1">No dietary conflicts or allergen violations detected</p>
        </div>
      )}

      {/* ── Refresh ── */}
      <button
        onClick={fetchShield}
        className="flex items-center gap-2 text-xs text-slate-500 hover:text-[#421018] transition"
      >
        <span className="material-symbols-outlined text-[14px]">refresh</span>
        Re-audit catalog
      </button>
    </div>
  );
};
