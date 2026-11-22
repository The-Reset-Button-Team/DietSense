/**
 * DietSense — useDailyRecommendations Hook
 * Fetches per-slot meal recommendations from POST /api/recommendations/daily
 * Supports per-slot shuffle via POST /api/recommendations/slot/{slot_id}?shuffle=true
 * Falls back gracefully when unauthenticated or backend unavailable.
 */

"use client";

import { useState, useEffect, useCallback, useRef } from "react";
import { apiClient } from "@/lib/api-client";
import { UserProfileData } from "@/context/AuthContext";
import { ActiveSlotsMap, BackendSlotRecommendation } from "@/lib/nutrition";
import { PantryItem, BudgetType, BudgetFilteringMode, DailyBudgetSummary } from "@/types";

// ─── Re-export so other files can import from here ───────────────────────────
export type { BackendSlotRecommendation };

// ─── Daily Totals ─────────────────────────────────────────────────────────────

export interface DailyNutritionTotals {
  calories: number;
  protein_g: number;
  carbs_g: number;
  fat_g: number;
  fiber_g: number;
}

// ─── API Response Shape ───────────────────────────────────────────────────────

interface DailyRecommendationsResponse {
  slots: Record<string, BackendSlotRecommendation[]>;
  totals: DailyNutritionTotals;
  active_slots?: string[];
  generated_at?: string;
  budget_summary?: DailyBudgetSummary;
}

// ─── Hook Input ───────────────────────────────────────────────────────────────

interface UseDailyRecommendationsInput {
  profile: UserProfileData | null;
  activeSlots: ActiveSlotsMap;
  pantryItems: PantryItem[];
  /** When false (unauthenticated), returns empty state and skips all API calls */
  enabled: boolean;
}

// ─── Hook Return ──────────────────────────────────────────────────────────────

export interface UseDailyRecommendationsReturn {
  slots: Record<string, BackendSlotRecommendation[]>;
  totals: DailyNutritionTotals | null;
  loading: boolean;
  error: string | null;
  refetch: () => void;
  shuffleSlot: (slotId: string) => Promise<void>;
  shufflingSlots: Set<string>;
  // Budget state (Batch 5)
  budgetAmount: number | null;
  budgetType: BudgetType;
  budgetMode: BudgetFilteringMode;
  budgetSummary: DailyBudgetSummary | null;
  setBudgetAmount: (amount: number | null) => void;
  setBudgetType: (type: BudgetType) => void;
  setBudgetMode: (mode: BudgetFilteringMode) => void;
  clearBudget: () => void;
}

// ─── Helpers ──────────────────────────────────────────────────────────────────

function calculateProfileCalories(profile: UserProfileData): number {
  return profile.daily_calorie_target || 1850;
}

function buildRequestBody(
  profile: UserProfileData,
  activeSlots: ActiveSlotsMap,
  pantryItems: PantryItem[],
  targetCalories: number,
  budgetAmount: number | null,
  budgetType: BudgetType,
  budgetMode: BudgetFilteringMode
) {
  const inStockNames = pantryItems.filter((p) => p.inStock).map((p) => p.name);

  return {
    user_profile: {
      goal: profile.goal,
      dietary_preference: profile.dietary_preference || profile.dietary_pref || "vegetarian",
      allergies: profile.allergies || [],
      calorie_target: targetCalories,
      budget_per_meal: budgetAmount || profile.budget_per_meal || 100,
      prep_time_limit: profile.prep_time_limit || 30,
    },
    active_slots: activeSlots,
    pantry_items: inStockNames,
    top_n: 5,
    shuffle: false,
    budget_amount: budgetAmount,
    budget_type: budgetType,
    budget_mode: budgetMode,
  };
}

// ─── Hook ─────────────────────────────────────────────────────────────────────

export function useDailyRecommendations({
  profile,
  activeSlots,
  pantryItems,
  enabled,
}: UseDailyRecommendationsInput): UseDailyRecommendationsReturn {
  const [slots, setSlots] = useState<Record<string, BackendSlotRecommendation[]>>({});
  const [totals, setTotals] = useState<DailyNutritionTotals | null>(null);
  const [loading, setLoading] = useState<boolean>(false);
  const [error, setError] = useState<string | null>(null);
  const [fetchTrigger, setFetchTrigger] = useState<number>(0);
  const [shufflingSlots, setShufflingSlots] = useState<Set<string>>(new Set());

  // Budget Filter State
  const [budgetAmount, setBudgetAmount] = useState<number | null>(null);
  const [budgetType, setBudgetType] = useState<BudgetType>("per_meal");
  const [budgetMode, setBudgetMode] = useState<BudgetFilteringMode>("within_budget");
  const [budgetSummary, setBudgetSummary] = useState<DailyBudgetSummary | null>(null);

  const abortRef = useRef<AbortController | null>(null);

  const refetch = useCallback(() => {
    setFetchTrigger((n) => n + 1);
  }, []);

  const clearBudget = useCallback(() => {
    setBudgetAmount(null);
    setBudgetMode("within_budget");
  }, []);

  // Main fetch effect
  const allergiesKey = JSON.stringify(profile?.allergies);

  useEffect(() => {
    if (!enabled || !profile) {
      setSlots({});
      setTotals(null);
      setBudgetSummary(null);
      setLoading(false);
      setError(null);
      return;
    }

    if (abortRef.current) {
      abortRef.current.abort();
    }
    const controller = new AbortController();
    abortRef.current = controller;

    let cancelled = false;

    (async () => {
      setLoading(true);
      setError(null);

      try {
        const targetCalories = calculateProfileCalories(profile);
        const body = buildRequestBody(
          profile,
          activeSlots,
          pantryItems,
          targetCalories,
          budgetAmount,
          budgetType,
          budgetMode
        );

        const data = await apiClient<DailyRecommendationsResponse>(
          "/api/recommendations/daily",
          {
            method: "POST",
            body: JSON.stringify(body),
            signal: controller.signal,
          }
        );

        if (!cancelled) {
          setSlots(data.slots || {});
          setTotals(data.totals || null);
          setBudgetSummary(data.budget_summary || null);
          setError(null);
        }
      } catch (err: any) {
        if (!cancelled && err?.name !== "AbortError") {
          setSlots({});
          setTotals(null);
          setBudgetSummary(null);
          setError(err?.message || "Failed to fetch daily recommendations");
        }
      } finally {
        if (!cancelled) {
          setLoading(false);
        }
      }
    })();

    return () => {
      cancelled = true;
      controller.abort();
    };
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [
    enabled,
    profile?.id,
    profile?.dietary_pref,
    profile?.dietary_preference,
    allergiesKey,
    profile?.budget_per_meal,
    profile?.prep_time_limit,
    profile?.goal,
    profile?.daily_calorie_target,
    fetchTrigger,
    budgetAmount,
    budgetType,
    budgetMode,
  ]);

  // Per-slot shuffle
  const shuffleSlot = useCallback(
    async (slotId: string) => {
      if (!enabled || !profile) return;

      setShufflingSlots((prev) => new Set(prev).add(slotId));

      try {
        const targetCalories = calculateProfileCalories(profile);
        const body = {
          user_profile: {
            goal: profile.goal,
            dietary_preference: profile.dietary_preference || profile.dietary_pref || "vegetarian",
            allergies: profile.allergies || [],
            calorie_target: targetCalories,
            budget_per_meal: budgetAmount || profile.budget_per_meal || 100,
            prep_time_limit: profile.prep_time_limit || 30,
          },
          pantry_items: pantryItems.filter((p) => p.inStock).map((p) => p.name),
          budget_amount: budgetAmount,
          budget_type: budgetType,
          budget_mode: budgetMode,
        };

        const results = await apiClient<BackendSlotRecommendation[]>(
          `/api/recommendations/slot/${slotId}?shuffle=true&top_n=5`,
          {
            method: "POST",
            body: JSON.stringify(body),
          }
        );

        setSlots((prev) => ({
          ...prev,
          [slotId]: results,
        }));
      } catch {
        // Silently ignore shuffle errors — keep existing slot data
      } finally {
        setShufflingSlots((prev) => {
          const next = new Set(prev);
          next.delete(slotId);
          return next;
        });
      }
    },
    [enabled, profile, pantryItems, budgetAmount, budgetType, budgetMode]
  );

  return {
    slots,
    totals,
    loading,
    error,
    refetch,
    shuffleSlot,
    shufflingSlots,
    budgetAmount,
    budgetType,
    budgetMode,
    budgetSummary,
    setBudgetAmount,
    setBudgetType,
    setBudgetMode,
    clearBudget,
  };
}
