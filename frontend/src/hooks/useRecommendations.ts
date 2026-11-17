/**
 * DietSense — useRecommendations Hook
 * Fetches personalised meal recommendations from the FastAPI backend.
 * Falls back gracefully when the user is not authenticated or the backend is unavailable.
 */

"use client";

import { useState, useEffect, useCallback, useRef } from "react";
import { apiClient } from "@/lib/api-client";
import { UserProfileData } from "@/context/AuthContext";
import { ActiveSlotsMap } from "@/lib/nutrition";
import { PantryItem } from "@/types";

// ─── Backend Response Types ───────────────────────────────────────────────────

export interface BackendRecommendation {
  item: {
    id: number;
    name: string;
    tags: string[];
    allergens: string[];
    cuisine: string;
    cost_estimate: number;
    prep_time: number;
    calories: number;
    protein_g: number;
    carbs_g: number;
    fat_g: number;
    food_category: string;
  };
  score: number;
  breakdown: Record<string, number>;
  reason: string;
}

// ─── Hook Input ───────────────────────────────────────────────────────────────

interface UseRecommendationsInput {
  profile: UserProfileData | null;
  activeSlots: ActiveSlotsMap;
  pantryItems: PantryItem[];
  /** When false (unauthenticated), returns null and skips all API calls */
  enabled: boolean;
}

// ─── Hook Return ──────────────────────────────────────────────────────────────

interface UseRecommendationsReturn {
  recommendations: BackendRecommendation[] | null;
  loading: boolean;
  error: string | null;
  refetch: () => void;
}

// ─── Helpers ─────────────────────────────────────────────────────────────────

function deriveDietaryPreference(profile: UserProfileData): "vegetarian" | "non-vegetarian" {
  // Derive from goal or any dietary hint on the profile; default to vegetarian
  // The profile doesn't have an explicit vegetarian flag yet, so we keep a sensible default
  return "vegetarian";
}

function buildRequestBody(
  profile: UserProfileData,
  activeSlots: ActiveSlotsMap,
  pantryItems: PantryItem[],
  targetCalories: number
) {
  const inStockNames = pantryItems.filter((p) => p.inStock).map((p) => p.name);

  return {
    user_profile: {
      goal: profile.goal,
      dietary_preference: deriveDietaryPreference(profile),
      allergies: (profile as any).allergies || [],
      calorie_target: targetCalories,
      budget_per_meal: (profile as any).budget_per_meal || 100,
      prep_time_limit: (profile as any).prep_time_limit || 30,
      top_n: 5,
    },
    active_slots: activeSlots,
    pantry_items: inStockNames,
  };
}

function calculateProfileCalories(profile: UserProfileData): number {
  // Use stored target if present, otherwise fall back to the profile value
  return profile.daily_calorie_target || 1850;
}

// ─── Hook ─────────────────────────────────────────────────────────────────────

export function useRecommendations({
  profile,
  activeSlots,
  pantryItems,
  enabled,
}: UseRecommendationsInput): UseRecommendationsReturn {
  const [recommendations, setRecommendations] = useState<BackendRecommendation[] | null>(null);
  const [loading, setLoading] = useState<boolean>(false);
  const [error, setError] = useState<string | null>(null);

  // Use a counter to trigger manual refetch
  const [fetchTrigger, setFetchTrigger] = useState<number>(0);

  // Track in-flight request to avoid stale updates
  const abortRef = useRef<AbortController | null>(null);

  const refetch = useCallback(() => {
    setFetchTrigger((n) => n + 1);
  }, []);

  useEffect(() => {
    // If not enabled (unauthenticated or explicitly disabled), clear and bail out
    if (!enabled || !profile) {
      setRecommendations(null);
      setLoading(false);
      setError(null);
      return;
    }

    // Cancel any previous in-flight request
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
        const body = buildRequestBody(profile, activeSlots, pantryItems, targetCalories);

        const data = await apiClient<BackendRecommendation[]>("/api/recommendations/", {
          method: "POST",
          body: JSON.stringify(body),
          signal: controller.signal,
        });

        if (!cancelled) {
          setRecommendations(data);
          setError(null);
        }
      } catch (err: any) {
        if (!cancelled && err?.name !== "AbortError") {
          // Silently fall back — the UI will use static data
          setRecommendations(null);
          setError(err?.message || "Failed to fetch recommendations");
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
    // fetchTrigger included so refetch() re-runs the effect
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [enabled, profile?.id, fetchTrigger]);

  return { recommendations, loading, error, refetch };
}
