/**
 * DietSense — SwapView (Phase 8B)
 * Dynamic meal swap with backend-scored alternatives, side-by-side macro delta,
 * staged confirmation (original plan preserved until user confirms), and
 * safety validation before applying any swap.
 */

"use client";

import React, { useState, useCallback, useEffect } from "react";
import { apiClient } from "@/lib/api-client";
import { useAuth } from "@/context/AuthContext";
import { CalculatedMealItem } from "@/lib/nutrition";

// ─── Types ───────────────────────────────────────────────────────────────────

interface SwapItem {
  id?: number;
  name: string;
  calories: number;
  protein_g: number;
  carbs_g: number;
  fat_g: number;
  fiber_g?: number;
  tags?: string[];
  allergens?: string[];
  food_category?: string;
  data_source?: string;
}

interface SwapAlternative {
  item: SwapItem;
  macro_match_pct: number;
  delta_calories: number;
  delta_protein_g: number;
  delta_carbs_g: number;
  delta_fat_g: number;
  delta_fiber_g: number;
  reason: string;
  score: number;
}

interface SwapResponse {
  current_meal: SwapItem;
  swap_alternatives: SwapAlternative[];
}

// ─── Props ───────────────────────────────────────────────────────────────────

interface SwapViewProps {
  targetCalories: number;
  activeMealItems?: CalculatedMealItem[];
  onApplySwap?: (slotKey: string, newMealName: string) => void;
}

// ─── Helpers ─────────────────────────────────────────────────────────────────

const SLOT_LABELS: Record<string, string> = {
  early_morning: "Early Morning",
  breakfast: "Breakfast",
  lunch: "Lunch",
  evening_snack: "Evening Snack",
  dinner: "Dinner",
};

const SLOT_ICONS: Record<string, string> = {
  early_morning: "☕",
  breakfast: "🥣",
  lunch: "🍱",
  evening_snack: "🍎",
  dinner: "🍽️",
};

function deltaColor(val: number): string {
  if (val > 0) return "text-red-600";
  if (val < 0) return "text-emerald-600";
  return "text-slate-500";
}

function deltaLabel(val: number, unit: string = ""): string {
  if (val > 0) return `+${val}${unit}`;
  if (val < 0) return `${val}${unit}`;
  return `0${unit}`;
}

function matchBadgeColor(pct: number): string {
  if (pct >= 90) return "bg-emerald-50 text-emerald-700 border-emerald-200";
  if (pct >= 75) return "bg-blue-50 text-blue-700 border-blue-200";
  return "bg-amber-50 text-amber-700 border-amber-200";
}

// ─── Component ───────────────────────────────────────────────────────────────

export const SwapView: React.FC<SwapViewProps> = ({
  targetCalories,
  activeMealItems = [],
  onApplySwap,
}) => {
  const { isAuthenticated } = useAuth();

  // Available slot keys derived from active meal items, or defaults
  const availableSlots: string[] =
    activeMealItems.length > 0
      ? [...new Set(activeMealItems.map((m) => m.key?.split("_")[0] || "breakfast"))]
      : ["breakfast", "lunch", "dinner"];

  const [selectedSlot, setSelectedSlot] = useState<string>(availableSlots[0] || "breakfast");
  const [swapData, setSwapData] = useState<SwapResponse | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  // Staged confirmation state
  const [pendingSwap, setPendingSwap] = useState<SwapAlternative | null>(null);
  const [confirmLoading, setConfirmLoading] = useState(false);
  const [confirmError, setConfirmError] = useState<string | null>(null);
  const [appliedSwap, setAppliedSwap] = useState<string | null>(null); // name of applied swap

  // ─── Build current meal from active items ────────────────────────────────
  const currentMealItem = activeMealItems.find((m) => {
    const slotBase = m.key?.split("_")[0] || "";
    return slotBase === selectedSlot || m.recipe?.slotLabel?.toLowerCase().includes(selectedSlot.replace("_", " "));
  });

  const currentMeal: SwapItem = currentMealItem
    ? {
        name: currentMealItem.backendName || currentMealItem.recipe.name,
        calories: currentMealItem.calories ?? 0,
        protein_g: currentMealItem.protein ?? 0,
        carbs_g: currentMealItem.carbs ?? 0,
        fat_g: currentMealItem.fat ?? 0,
        fiber_g: currentMealItem.fibre ?? 0,
      }
    : {
        name: `Current ${SLOT_LABELS[selectedSlot] || selectedSlot} meal`,
        calories: Math.round(targetCalories / 3),
        protein_g: 20,
        carbs_g: 50,
        fat_g: 10,
      };

  const fetchSwaps = useCallback(async () => {
    if (!isAuthenticated) return;
    setLoading(true);
    setError(null);
    setSwapData(null);
    setPendingSwap(null);
    setConfirmError(null);
    setAppliedSwap(null);

    try {
      const result = await apiClient<SwapResponse>("/api/recommendations/swap", {
        method: "POST",
        body: JSON.stringify({
          slot_id: selectedSlot,
          current_meal: currentMeal,
          target_calories: targetCalories,
          top_n: 5,
        }),
      });
      setSwapData(result);
    } catch (err: any) {
      setError(err?.message || "Failed to fetch swap alternatives");
    } finally {
      setLoading(false);
    }
  }, [isAuthenticated, selectedSlot, targetCalories, currentMeal.name]);

  // Auto-fetch when slot changes
  useEffect(() => {
    fetchSwaps();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [selectedSlot]);

  // ─── Staged confirm: validate then apply ─────────────────────────────────
  const handleConfirmSwap = async () => {
    if (!pendingSwap) return;
    setConfirmLoading(true);
    setConfirmError(null);

    try {
      // Safety validation before applying
      await apiClient("/api/recommendations/swap/validate", {
        method: "POST",
        body: JSON.stringify({ candidate: pendingSwap.item }),
      });

      // Safe — apply swap
      setAppliedSwap(pendingSwap.item.name);
      if (onApplySwap) {
        const slotKey = currentMealItem?.key || selectedSlot;
        onApplySwap(slotKey, pendingSwap.item.name);
      }
      setPendingSwap(null);
    } catch (err: any) {
      const detail = err?.detail || err?.message || "Swap blocked by safety shield";
      const reason = typeof detail === "object" ? detail.reason : detail;
      setConfirmError(`🚫 ${reason}`);
    } finally {
      setConfirmLoading(false);
    }
  };

  // ─── Unauthenticated ─────────────────────────────────────────────────────
  if (!isAuthenticated) {
    return (
      <div className="relative z-10 space-y-4">
        <div className="rounded-2xl bg-white p-6 border border-[#e8ded3] text-center shadow-sm">
          <span className="text-3xl">🔄</span>
          <h3 className="text-base font-serif text-[#421018] mt-3">Sign in to generate meal swaps</h3>
          <p className="text-xs text-slate-500 mt-1">Swap alternatives are personalised to your calorie target and dietary profile.</p>
        </div>
      </div>
    );
  }

  return (
    <div className="relative z-10 space-y-4">
      {/* ── Slot Selector ── */}
      <div className="rounded-2xl bg-white p-4 border border-[#e8ded3] shadow-sm">
        <h3 className="text-sm font-serif text-[#421018] mb-3">🔄 Mindful Swap Generator</h3>
        <p className="text-xs text-slate-500 mb-3">
          Select a meal slot to generate safety-screened alternatives matching your {targetCalories} kcal target:
        </p>
        <div className="flex flex-wrap gap-2">
          {availableSlots.map((slot) => (
            <button
              key={slot}
              onClick={() => setSelectedSlot(slot)}
              className={`px-3 py-1.5 rounded-full text-xs font-medium border transition-all ${
                selectedSlot === slot
                  ? "bg-[#581825] text-white border-[#581825]"
                  : "bg-[#faf7f2] text-slate-600 border-[#e2d6c9] hover:border-[#581825]"
              }`}
            >
              {SLOT_ICONS[slot] || "🍴"} {SLOT_LABELS[slot] || slot}
            </button>
          ))}
        </div>
      </div>

      {/* ── Current Meal Summary ── */}
      <div className="rounded-2xl bg-[#faf7f2] p-4 border border-[#e2d6c9] shadow-sm">
        <div className="flex items-center justify-between mb-2">
          <h4 className="text-xs font-semibold text-slate-500 uppercase tracking-wide">Current Plan</h4>
          <button
            onClick={fetchSwaps}
            disabled={loading}
            className="flex items-center gap-1 text-xs text-[#581825] hover:underline disabled:opacity-40"
          >
            <span className={`material-symbols-outlined text-[14px] ${loading ? "animate-spin" : ""}`}>refresh</span>
            {loading ? "Fetching…" : "Find alternatives"}
          </button>
        </div>
        <p className="text-sm font-serif text-[#421018] font-semibold">{currentMeal.name}</p>
        <div className="flex flex-wrap gap-2 mt-1.5">
          {[
            { label: `${Math.round(currentMeal.calories)} kcal`, color: "bg-primary/10 text-primary" },
            { label: `${Math.round(currentMeal.protein_g)}g P`, color: "bg-primary/10 text-primary" },
            { label: `${Math.round(currentMeal.carbs_g)}g C`, color: "bg-amber-500/10 text-amber-700" },
            { label: `${Math.round(currentMeal.fat_g)}g F`, color: "bg-secondary/10 text-secondary" },
          ].map((tag) => (
            <span key={tag.label} className={`px-2 py-0.5 rounded-full text-[11px] font-medium ${tag.color}`}>
              {tag.label}
            </span>
          ))}
        </div>
      </div>

      {/* ── Applied swap confirmation ── */}
      {appliedSwap && (
        <div className="rounded-2xl bg-emerald-50 p-4 border border-emerald-200 shadow-sm flex items-center gap-3">
          <span className="text-2xl">✅</span>
          <div>
            <p className="text-sm font-semibold text-emerald-700">Swap applied!</p>
            <p className="text-xs text-emerald-600 mt-0.5">{appliedSwap} is now your {SLOT_LABELS[selectedSlot]} meal.</p>
          </div>
          <button onClick={() => setAppliedSwap(null)} className="ml-auto text-emerald-500 hover:text-emerald-700">
            <span className="material-symbols-outlined text-[18px]">close</span>
          </button>
        </div>
      )}

      {/* ── Staged confirmation modal ── */}
      {pendingSwap && !appliedSwap && (
        <div className="rounded-2xl bg-white p-5 border-2 border-[#581825] shadow-md space-y-4">
          <h4 className="text-sm font-serif text-[#421018] font-semibold">Review Swap</h4>

          <div className="grid grid-cols-2 gap-3">
            {/* Current */}
            <div className="p-3 rounded-xl bg-slate-50 border border-slate-200">
              <p className="text-[10px] text-slate-400 font-semibold uppercase mb-1">Current</p>
              <p className="text-xs font-semibold text-slate-700 leading-tight">{currentMeal.name}</p>
              <div className="text-[11px] text-slate-500 mt-1 space-y-0.5">
                <div>{Math.round(currentMeal.calories)} kcal</div>
                <div>{Math.round(currentMeal.protein_g)}g P · {Math.round(currentMeal.carbs_g)}g C · {Math.round(currentMeal.fat_g)}g F</div>
              </div>
            </div>
            {/* Swap */}
            <div className="p-3 rounded-xl bg-emerald-50 border border-emerald-200">
              <p className="text-[10px] text-emerald-500 font-semibold uppercase mb-1">Swap to</p>
              <p className="text-xs font-semibold text-emerald-800 leading-tight">{pendingSwap.item.name}</p>
              <div className="text-[11px] text-emerald-700 mt-1 space-y-0.5">
                <div>{Math.round(pendingSwap.item.calories)} kcal</div>
                <div>{Math.round(pendingSwap.item.protein_g)}g P · {Math.round(pendingSwap.item.carbs_g)}g C · {Math.round(pendingSwap.item.fat_g)}g F</div>
              </div>
            </div>
          </div>

          {/* Macro delta summary */}
          <div className="flex flex-wrap gap-3 text-xs font-medium">
            {[
              { label: "Calories", val: pendingSwap.delta_calories, unit: " kcal" },
              { label: "Protein", val: pendingSwap.delta_protein_g, unit: "g" },
              { label: "Carbs", val: pendingSwap.delta_carbs_g, unit: "g" },
              { label: "Fat", val: pendingSwap.delta_fat_g, unit: "g" },
            ].map(({ label, val, unit }) => (
              <div key={label} className="flex items-center gap-1">
                <span className="text-slate-400">{label}:</span>
                <span className={`font-bold ${deltaColor(val)}`}>{deltaLabel(val, unit)}</span>
              </div>
            ))}
          </div>

          {confirmError && (
            <p className="text-xs text-red-600 bg-red-50 border border-red-200 p-2 rounded-lg">{confirmError}</p>
          )}

          <div className="flex gap-3">
            <button
              onClick={() => { setPendingSwap(null); setConfirmError(null); }}
              className="flex-1 py-2 text-xs rounded-xl border border-slate-200 text-slate-600 hover:bg-slate-50 transition"
            >
              Cancel
            </button>
            <button
              onClick={handleConfirmSwap}
              disabled={confirmLoading}
              className="flex-1 py-2 text-xs rounded-xl bg-[#581825] text-white hover:bg-[#421018] transition disabled:opacity-50"
            >
              {confirmLoading ? "Validating…" : "Confirm Swap"}
            </button>
          </div>
        </div>
      )}

      {/* ── Loading ── */}
      {loading && !swapData && (
        <div className="rounded-2xl bg-white p-6 border border-[#e8ded3] shadow-sm flex items-center gap-3">
          <span className="material-symbols-outlined animate-spin text-[#581825]">refresh</span>
          <p className="text-sm text-slate-500">Generating safety-screened alternatives…</p>
        </div>
      )}

      {/* ── Error ── */}
      {error && (
        <div className="rounded-2xl bg-white p-5 border border-red-200 shadow-sm">
          <p className="text-sm text-red-700">⚠️ {error}</p>
          <button onClick={fetchSwaps} className="mt-2 text-xs text-[#581825] underline">Retry</button>
        </div>
      )}

      {/* ── Alternatives Grid ── */}
      {swapData && swapData.swap_alternatives.length > 0 && (
        <div className="rounded-2xl bg-white p-5 border border-[#e8ded3] shadow-sm">
          <h4 className="text-sm font-serif text-[#421018] mb-3">
            🌿 {swapData.swap_alternatives.length} Safe Alternatives
          </h4>
          <div className="space-y-3">
            {swapData.swap_alternatives.map((alt, idx) => (
              <div
                key={alt.item.id ?? idx}
                className="p-4 rounded-xl bg-[#faf7f2] border border-[#e2d6c9] hover:border-[#581825] transition-all"
              >
                <div className="flex items-start justify-between gap-3 flex-wrap">
                  <div className="flex-1 min-w-0">
                    {/* Match badge */}
                    <span className={`inline-block text-[10px] font-bold px-2 py-0.5 rounded-full border mb-1.5 ${matchBadgeColor(alt.macro_match_pct)}`}>
                      {alt.macro_match_pct}% Macro Match
                    </span>
                    <h5 className="text-sm font-semibold text-[#421018] font-serif leading-tight">{alt.item.name}</h5>

                    {/* Nutrition row */}
                    <div className="flex flex-wrap gap-1.5 mt-1.5">
                      <span className="px-1.5 py-0.5 rounded-full text-[11px] bg-primary/10 text-primary font-medium">
                        {Math.round(alt.item.calories)} kcal
                      </span>
                      <span className="px-1.5 py-0.5 rounded-full text-[11px] bg-primary/10 text-primary font-medium">
                        {Math.round(alt.item.protein_g)}g P
                      </span>
                      <span className="px-1.5 py-0.5 rounded-full text-[11px] bg-amber-500/10 text-amber-700 font-medium">
                        {Math.round(alt.item.carbs_g)}g C
                      </span>
                      <span className="px-1.5 py-0.5 rounded-full text-[11px] bg-secondary/10 text-secondary font-medium">
                        {Math.round(alt.item.fat_g)}g F
                      </span>
                    </div>

                    {/* Delta row */}
                    <div className="flex flex-wrap gap-3 mt-2 text-[11px] font-medium">
                      {[
                        { label: "Cal", val: alt.delta_calories, unit: " kcal" },
                        { label: "P", val: alt.delta_protein_g, unit: "g" },
                        { label: "C", val: alt.delta_carbs_g, unit: "g" },
                        { label: "F", val: alt.delta_fat_g, unit: "g" },
                      ].map(({ label, val, unit }) => (
                        <span key={label} className={`flex items-center gap-0.5 ${deltaColor(val)}`}>
                          <span className="text-slate-400">{label}:</span>
                          {deltaLabel(val, unit)}
                        </span>
                      ))}
                    </div>

                    {alt.reason && (
                      <p className="text-[11px] text-slate-400 italic mt-1.5">{alt.reason}</p>
                    )}
                  </div>

                  {/* Select button */}
                  <button
                    onClick={() => {
                      setPendingSwap(alt);
                      setConfirmError(null);
                      setAppliedSwap(null);
                    }}
                    disabled={!!pendingSwap}
                    className="shrink-0 px-4 py-2 text-xs rounded-xl bg-[#581825] text-white hover:bg-[#421018] transition disabled:opacity-40"
                  >
                    Select
                  </button>
                </div>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* ── Empty state ── */}
      {swapData && swapData.swap_alternatives.length === 0 && (
        <div className="rounded-2xl bg-white p-6 border border-[#e8ded3] shadow-sm text-center">
          <span className="text-3xl">🤷</span>
          <p className="text-sm text-slate-600 mt-3">No safe alternatives found for this slot</p>
          <p className="text-xs text-slate-400 mt-1">All candidates were filtered by your dietary restrictions or allergen profile.</p>
          <button onClick={fetchSwaps} className="mt-3 text-xs text-[#581825] underline">Try again</button>
        </div>
      )}
    </div>
  );
};
