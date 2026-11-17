/**
 * DietSense — useSlotRegenerate Hook
 * Calls the backend to get alternative meal recommendations for a specific meal slot.
 * Returns loading/error state and the resulting BackendRecommendation alternatives.
 */

"use client";

import { useState, useCallback } from "react";
import { apiClient } from "@/lib/api-client";
import { UserProfileData } from "@/context/AuthContext";
import { BackendRecommendation } from "./useRecommendations";

// ─── Hook Return ──────────────────────────────────────────────────────────────

interface UseSlotRegenerateReturn {
  alternatives: BackendRecommendation[];
  loading: boolean;
  error: string | null;
  /** Call this to trigger a regeneration for the slot */
  regenerate: (userProfile: UserProfileData) => Promise<BackendRecommendation[]>;
}

// ─── Hook ─────────────────────────────────────────────────────────────────────

export function useSlotRegenerate(slotId: string): UseSlotRegenerateReturn {
  const [alternatives, setAlternatives] = useState<BackendRecommendation[]>([]);
  const [loading, setLoading] = useState<boolean>(false);
  const [error, setError] = useState<string | null>(null);

  const regenerate = useCallback(
    async (userProfile: UserProfileData): Promise<BackendRecommendation[]> => {
      setLoading(true);
      setError(null);

      try {
        const body = {
          user_profile: {
            goal: userProfile.goal,
            // Derive dietary preference; default to vegetarian
            dietary_preference: "vegetarian",
            allergies: (userProfile as any).allergies || [],
            calorie_target: userProfile.daily_calorie_target || 1850,
            budget_per_meal: (userProfile as any).budget_per_meal || 100,
            prep_time_limit: (userProfile as any).prep_time_limit || 30,
            top_n: 5,
          },
        };

        const data = await apiClient<BackendRecommendation[]>(
          `/api/recommendations/slot/${encodeURIComponent(slotId)}`,
          {
            method: "POST",
            body: JSON.stringify(body),
          }
        );

        setAlternatives(data);
        setError(null);
        return data;
      } catch (err: any) {
        const msg = err?.message || "Failed to regenerate slot recommendations";
        setError(msg);
        setAlternatives([]);
        return [];
      } finally {
        setLoading(false);
      }
    },
    [slotId]
  );

  return { alternatives, loading, error, regenerate };
}
