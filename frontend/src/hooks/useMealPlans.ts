/**
 * DietSense — useMealPlans Hook
 * Provides meal plan persistence, historical browsing, status management
 * (generated -> accepted -> completed), and weekly calendar views.
 * Persists data to the local SQLite database via FastAPI.
 */

"use client";

import { useState, useEffect, useCallback } from "react";
import { apiClient } from "@/lib/api-client";
import { CalculatedMealItem } from "@/lib/nutrition";

export type MealPlanStatus = "generated" | "accepted" | "completed";

export interface SavedMealPlanItem {
  slot: string;
  name: string;
  calories: number;
  protein_g: number;
  carbs_g: number;
  fat_g: number;
  fiber_g?: number;
  recipe_id?: number;
  reason?: string;
  data_source?: string;
}

export interface SavedMealPlan {
  id: string;
  user_id: string;
  date: string;
  target_calories: number;
  items: SavedMealPlanItem[];
  status: MealPlanStatus;
  created_at: string;
  updated_at?: string;
}

export interface WeeklyDayPlan {
  date: string;
  plan: SavedMealPlan | null;
}

export interface WeeklyScheduleResponse {
  start_date: string;
  end_date: string;
  days: WeeklyDayPlan[];
}

interface UseMealPlansInput {
  enabled: boolean;
}

export interface UseMealPlansReturn {
  plans: SavedMealPlan[];
  todayPlan: SavedMealPlan | null;
  weeklySchedule: WeeklyDayPlan[];
  loading: boolean;
  error: string | null;
  isSaving: boolean;
  saveTodayPlan: (
    items: CalculatedMealItem[],
    targetCalories: number,
    status?: MealPlanStatus,
    customDate?: string
  ) => Promise<SavedMealPlan | null>;
  updateStatus: (planId: string, newStatus: MealPlanStatus) => Promise<SavedMealPlan | null>;
  deletePlan: (planId: string) => Promise<boolean>;
  refetchPlans: () => Promise<void>;
  refetchWeeklySchedule: (startDate?: string) => Promise<void>;
}

export function useMealPlans({ enabled }: UseMealPlansInput): UseMealPlansReturn {
  const [plans, setPlans] = useState<SavedMealPlan[]>([]);
  const [weeklySchedule, setWeeklySchedule] = useState<WeeklyDayPlan[]>([]);
  const [loading, setLoading] = useState<boolean>(false);
  const [isSaving, setIsSaving] = useState<boolean>(false);
  const [error, setError] = useState<string | null>(null);

  const todayStr = new Date().toISOString().split("T")[0];

  // 1. Fetch user's saved meal plans
  const fetchPlans = useCallback(async () => {
    if (!enabled) {
      setPlans([]);
      return;
    }
    setLoading(true);
    setError(null);
    try {
      const data = await apiClient<SavedMealPlan[]>("/api/meal-plans");
      setPlans(Array.isArray(data) ? data : []);
    } catch (err: any) {
      // Backend not ready or offline fallback
      setError(err?.message || "Failed to load meal plans");
    } finally {
      setLoading(false);
    }
  }, [enabled]);

  // 2. Fetch weekly schedule
  const fetchWeeklySchedule = useCallback(
    async (startDate?: string) => {
      if (!enabled) {
        setWeeklySchedule([]);
        return;
      }
      try {
        const query = startDate ? `?start_date=${encodeURIComponent(startDate)}` : "";
        const data = await apiClient<WeeklyScheduleResponse>(`/api/meal-plans/weekly${query}`);
        if (data && Array.isArray(data.days)) {
          setWeeklySchedule(data.days);
        }
      } catch {
        // Fallback gracefully
      }
    },
    [enabled]
  );

  useEffect(() => {
    fetchPlans();
    fetchWeeklySchedule();
  }, [fetchPlans, fetchWeeklySchedule]);

  // Determine current active plan for today if saved
  const todayPlan = plans.find((p) => p.date === todayStr) || null;

  // 3. Save / Upsert today's meal plan
  const saveTodayPlan = useCallback(
    async (
      items: CalculatedMealItem[],
      targetCalories: number,
      status: MealPlanStatus = "accepted",
      customDate?: string
    ): Promise<SavedMealPlan | null> => {
      if (!enabled) return null;

      setIsSaving(true);
      setError(null);

      const targetDate = customDate || todayStr;

      // Map CalculatedMealItems into persistable items
      const mappedItems: SavedMealPlanItem[] = items.map((i) => ({
        slot: String(i.key),
        name: i.backendName || i.recipe.name,
        calories: i.calories,
        protein_g: i.protein,
        carbs_g: i.carbs,
        fat_g: i.fat,
        fiber_g: i.fibre || (i as any).fiber_g || 0,
        recipe_id: i.recipe.id,
        reason: i.backendReason,
        data_source: i.dataSource,
      }));

      // If a plan already exists for this date, preserve its ID so the backend updates it
      const existingPlan = plans.find((p) => p.date === targetDate);

      const payload = {
        id: existingPlan?.id,
        date: targetDate,
        target_calories: targetCalories,
        items: mappedItems,
        status,
      };

      try {
        const saved = await apiClient<SavedMealPlan>("/api/meal-plans", {
          method: "POST",
          body: JSON.stringify(payload),
        });

        // Update local state immediately
        setPlans((prev) => {
          const filtered = prev.filter((p) => p.id !== saved.id);
          return [saved, ...filtered];
        });

        // Refresh weekly schedule
        fetchWeeklySchedule();

        return saved;
      } catch (err: any) {
        setError(err?.message || "Failed to save meal plan");
        return null;
      } finally {
        setIsSaving(false);
      }
    },
    [enabled, todayStr, plans, fetchWeeklySchedule]
  );

  // 4. Update status of existing meal plan (generated -> accepted -> completed)
  const updateStatus = useCallback(
    async (planId: string, newStatus: MealPlanStatus): Promise<SavedMealPlan | null> => {
      if (!enabled) return null;

      try {
        const updated = await apiClient<SavedMealPlan>(`/api/meal-plans/${planId}/status`, {
          method: "PATCH",
          body: JSON.stringify({ status: newStatus }),
        });

        setPlans((prev) => prev.map((p) => (p.id === planId ? updated : p)));
        setWeeklySchedule((prev) =>
          prev.map((d) => (d.plan && d.plan.id === planId ? { ...d, plan: updated } : d))
        );
        return updated;
      } catch (err: any) {
        setError(err?.message || "Failed to update meal plan status");
        return null;
      }
    },
    [enabled]
  );

  // 5. Delete plan
  const deletePlan = useCallback(
    async (planId: string): Promise<boolean> => {
      if (!enabled) return false;

      try {
        await apiClient(`/api/meal-plans/${planId}`, { method: "DELETE" });
        setPlans((prev) => prev.filter((p) => p.id !== planId));
        setWeeklySchedule((prev) =>
          prev.map((d) => (d.plan && d.plan.id === planId ? { ...d, plan: null } : d))
        );
        return true;
      } catch {
        return false;
      }
    },
    [enabled]
  );

  return {
    plans,
    todayPlan,
    weeklySchedule,
    loading,
    error,
    isSaving,
    saveTodayPlan,
    updateStatus,
    deletePlan,
    refetchPlans: fetchPlans,
    refetchWeeklySchedule: fetchWeeklySchedule,
  };
}
