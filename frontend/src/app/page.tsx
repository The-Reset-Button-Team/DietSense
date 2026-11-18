"use client";

import { useState, useMemo, useEffect, Suspense } from "react";
import { useSearchParams } from "next/navigation";
import { GoalType, Gender, MealFrequency, EffortLevel, RecipeData, PantryItem } from "@/types";
import { RECIPE_CATALOG } from "@/data/recipes";
import { INITIAL_PANTRY_ITEMS } from "@/data/pantry";
import {
  calculateBMR,
  calculateTDEE,
  calculateTargetCalories,
  calculateMacroGrams,
  calculateMealPlanItems,
  ActiveSlotsMap,
  CalculatedMealItem,
} from "@/lib/nutrition";
import { useAuth } from "@/context/AuthContext";
import { apiClient } from "@/lib/api-client";
import { useDailyRecommendations } from "@/hooks/useDailyRecommendations";

import { Header } from "@/components/Header";
import { TabNav, TabType } from "@/components/TabNav";
import { MealPlanView } from "@/components/MealPlanView";
import { PantryScanner } from "@/components/PantryScanner";
import { ProfileStudio } from "@/components/ProfileStudio";
import { SwapView } from "@/components/SwapView";
import { SafetyShield } from "@/components/SafetyShield";
import { RecipeModal } from "@/components/RecipeModal";
import { AuthModal } from "@/components/auth/AuthModal";
import { ProgressAnalytics } from "@/components/ProgressAnalytics";
import { AIAssistantView } from "@/components/ai/AIAssistantView";
import { AIExplanationModal } from "@/components/ai/AIExplanationModal";
import { CookingInstructionsModal } from "@/components/ai/CookingInstructionsModal";
import { PantryCookAssistant } from "@/components/ai/PantryCookAssistant";
import { RecipeSuggestionView } from "@/components/ai/RecipeSuggestionView";

function MainApp() {
  const { user, updateProfile, isAuthenticated } = useAuth();
  const searchParams = useSearchParams();
  const queryTab = searchParams.get("tab") as TabType | null;

  const [activeTab, setActiveTab] = useState<TabType>(queryTab || "today");
  const [isAuthModalOpen, setIsAuthModalOpen] = useState<boolean>(false);

  useEffect(() => {
    if (queryTab && ["today", "pantry", "profile", "swap", "safety", "progress", "ai"].includes(queryTab)) {
      setActiveTab(queryTab);
    }
  }, [queryTab]);

  // Profile Biometrics State (initialized from user or defaults)
  const [goal, setGoal] = useState<GoalType>(user?.goal || "lose_weight");
  const [weight, setWeight] = useState<number>(user?.weight_kg || 75);
  const [height, setHeight] = useState<number>(user?.height_cm || 175);
  const [age, setAge] = useState<number>(user?.age || 26);
  const [gender, setGender] = useState<Gender>(user?.gender || "male");
  const [activity, setActivity] = useState<number>(1.375);

  // Sync state if auth user updates
  useEffect(() => {
    if (user) {
      setGoal(user.goal);
      setWeight(user.weight_kg);
      setHeight(user.height_cm);
      setAge(user.age);
      setGender(user.gender);
    }
  }, [user]);

  // Solo Cook & Routine Settings
  const [isSoloCook, setIsSoloCook] = useState<boolean>(user?.is_solo_cook ?? true);
  const [mealFrequency, setMealFrequency] = useState<MealFrequency>(
    (user?.active_meal_frequency as MealFrequency) || "3_meals"
  );
  const [weekdayBreakfastEffort, setWeekdayBreakfastEffort] = useState<EffortLevel>("low");
  const [weekdayLunchEffort, setWeekdayLunchEffort] = useState<EffortLevel>("moderate");

  // Active Slots Map
  const [activeSlots, setActiveSlots] = useState<ActiveSlotsMap>({
    early_morning: false,
    breakfast: true,
    lunch: true,
    evening_snack: false,
    dinner: true,
  });

  // Pantry State
  const [pantryItems, setPantryItems] = useState<PantryItem[]>(INITIAL_PANTRY_ITEMS);

  // Load pantry items from backend on mount (authenticated users only)
  useEffect(() => {
    if (!user) return;

    let cancelled = false;

    (async () => {
      try {
        const backendItems = await apiClient<
          Array<{ id: number | string; name: string; category: string; quantity: string; inStock: boolean; source?: string }>
        >("/api/pantry/");

        if (cancelled) return;

        const mapped: PantryItem[] = backendItems.map((item) => ({
          id: String(item.id),
          name: item.name,
          category: item.category,
          quantity: item.quantity,
          inStock: item.inStock,
        }));

        // Merge: backend items take priority (name-based dedup)
        setPantryItems((prev) => {
          const backendNames = new Set(mapped.map((i) => i.name.toLowerCase()));
          const kept = prev.filter((p) => !backendNames.has(p.name.toLowerCase()));
          return [...mapped, ...kept];
        });
      } catch {
        // Backend offline — silently keep INITIAL_PANTRY_ITEMS
      }
    })();

    return () => {
      cancelled = true;
    };
  }, [user]);

  // Recipe Modal State
  const [activeRecipeModal, setActiveRecipeModal] = useState<RecipeData | null>(null);

  // AI Feature State
  const [explainModal, setExplainModal] = useState<{ foodId: number; foodName: string } | null>(null);
  const [cookingModal, setCookingModal] = useState<{ foodId: number; foodName: string } | null>(null);
  const [askAIMealContext, setAskAIMealContext] = useState<{ id: number; name: string } | null>(null);

  // Metabolic Calculations
  const bmr = useMemo(() => calculateBMR(weight, height, age, gender), [weight, height, age, gender]);
  const tdee = useMemo(() => calculateTDEE(bmr, activity), [bmr, activity]);
  const targetCalories = useMemo(() => calculateTargetCalories(tdee, goal), [tdee, goal]);
  const macros = useMemo(() => calculateMacroGrams(targetCalories), [targetCalories]);

  const adjText =
    goal === "lose_weight"
      ? "-400 kcal (Cut Deficit)"
      : goal === "gain_weight"
      ? "+300 kcal (Lean Surplus)"
      : "0 kcal (Maintenance)";

  // Handlers
  const applyMealFrequency = (freq: MealFrequency) => {
    setMealFrequency(freq);
    updateProfile({ active_meal_frequency: freq });
    if (freq === "2_meals") {
      setActiveSlots({ early_morning: false, breakfast: false, lunch: true, evening_snack: false, dinner: true });
    } else if (freq === "3_meals") {
      setActiveSlots({ early_morning: false, breakfast: true, lunch: true, evening_snack: false, dinner: true });
    } else if (freq === "4_meals") {
      setActiveSlots({ early_morning: false, breakfast: true, lunch: true, evening_snack: true, dinner: true });
    } else if (freq === "5_meals") {
      setActiveSlots({ early_morning: true, breakfast: true, lunch: true, evening_snack: true, dinner: true });
    }
  };

  const toggleSlot = (slotKey: keyof ActiveSlotsMap) => {
    const updated = { ...activeSlots, [slotKey]: !activeSlots[slotKey] };
    const activeCount = Object.values(updated).filter(Boolean).length;
    if (activeCount === 0) return;
    setActiveSlots(updated);
    setMealFrequency("custom");
  };

  const togglePantryItem = (id: string) => {
    setPantryItems((prev) =>
      prev.map((item) => (item.id === id ? { ...item, inStock: !item.inStock } : item))
    );
    // Fire-and-forget sync to backend
    if (user) {
      apiClient(`/api/pantry/${id}/toggle`, { method: "PATCH" }).catch(() => {});
    }
  };

  const handleAddManualPantryItem = (name: string) => {
    const newItem: PantryItem = {
      id: Date.now().toString(),
      name,
      category: "My Custom Item",
      quantity: "1 unit",
      inStock: true,
    };
    setPantryItems((prev) => [newItem, ...prev]);
  };

  const handleAddBatchPantryItems = (items: Array<{ name: string; category?: string; quantity?: string }>) => {
    const newItems: PantryItem[] = items.map((item, idx) => ({
      id: `${Date.now()}_${idx}`,
      name: item.name,
      category: item.category || "Scanned Item",
      quantity: item.quantity || "1 unit",
      inStock: true,
    }));
    setPantryItems((prev) => {
      const existingNames = new Set(prev.map((p) => p.name.toLowerCase()));
      const updatedExisting = prev.map((p) => {
        if (items.some((i) => i.name.toLowerCase() === p.name.toLowerCase())) {
          return { ...p, inStock: true };
        }
        return p;
      });
      const trulyNew = newItems.filter((i) => !existingNames.has(i.name.toLowerCase()));
      return [...trulyNew, ...updatedExisting];
    });
  };

  // Selected custom recipe per slot (overrides auto-selection if user manually swaps)
  const [customSelectedRecipes, setCustomSelectedRecipes] = useState<Record<string, string>>({});

  const handleSelectAlternative = (slotKey: string, recipeName: string) => {
    setCustomSelectedRecipes((prev) => ({
      ...prev,
      [slotKey]: recipeName,
    }));
  };

  const handleApplyPantryToMealPlan = () => {
    // Reset manual overrides so smart pantry-first prioritization auto-selects best recipes for all slots
    setCustomSelectedRecipes({});
    setActiveTab("today");
  };

  // Calculated Meal Plan Items
  const mealPlanDisplayItems = useMemo(
    () =>
      calculateMealPlanItems(
        activeSlots,
        targetCalories,
        macros,
        weekdayBreakfastEffort,
        weekdayLunchEffort,
        RECIPE_CATALOG,
        pantryItems,
        customSelectedRecipes,
        true
      ),
    [
      activeSlots,
      targetCalories,
      macros,
      weekdayBreakfastEffort,
      weekdayLunchEffort,
      pantryItems,
      customSelectedRecipes,
    ]
  );

  // ─── Backend Daily Recommendations (authenticated users only) ─────────────
  const {
    slots: dailySlots,
    totals: dailyTotals,
    loading: recommendationsLoading,
    error: recommendationsError,
    refetch: refetchRecommendations,
    shuffleSlot,
    shufflingSlots,
  } = useDailyRecommendations({
    profile: user,
    activeSlots,
    pantryItems,
    enabled: isAuthenticated && !!user,
  });

  /**
   * Merge backend per-slot recommendations into static meal plan items.
   * For each active slot, slot[0] (top recommendation) overrides nutrition values.
   * Passes all alternatives as backendAlternatives for the Swap modal.
   * Falls back to mealPlanDisplayItems when no backend data available.
   */
  const activeMealItems = useMemo((): CalculatedMealItem[] => {
    const hasBackendData = Object.keys(dailySlots).length > 0;
    if (!hasBackendData) {
      return mealPlanDisplayItems;
    }

    return mealPlanDisplayItems.map((item) => {
      const slotRecs = dailySlots[item.key];
      if (!slotRecs || slotRecs.length === 0) return item;

      const topRec = slotRecs[0];
      return {
        ...item,
        // Override nutritional numbers with real backend values
        calories: Math.round(topRec.item.calories),
        protein: Math.round(topRec.item.protein_g),
        carbs: Math.round(topRec.item.carbs_g),
        fat: Math.round(topRec.item.fat_g),
        fibre: topRec.item.fiber_g > 0 ? topRec.item.fiber_g : item.fibre,
        // Enrich with backend metadata
        backendName: topRec.item.name,
        backendReason: topRec.reason,
        backendScore: topRec.score,
        backendBreakdown: topRec.breakdown,
        backendAlternatives: slotRecs,
        dataSource: topRec.item.data_source,
      };
    });
  }, [mealPlanDisplayItems, dailySlots]);

  // Use backend daily totals when available, otherwise sum from activeMealItems
  const totalPlannedCals = dailyTotals?.calories ?? activeMealItems.reduce((acc, item) => acc + item.calories, 0);
  const totalPlannedProt = dailyTotals?.protein_g ?? activeMealItems.reduce((acc, item) => acc + item.protein, 0);
  const totalPlannedCarbs = dailyTotals?.carbs_g ?? activeMealItems.reduce((acc, item) => acc + item.carbs, 0);
  const totalPlannedFat = dailyTotals?.fat_g ?? activeMealItems.reduce((acc, item) => acc + item.fat, 0);
  const totalPlannedFiber = dailyTotals?.fiber_g ?? activeMealItems.reduce((acc, item) => acc + (item.fibre || 0), 0);

  const inStockPantryNames = useMemo(
    () => pantryItems.filter((i) => i.inStock).map((i) => i.name),
    [pantryItems]
  );

  return (
    <div className="min-h-screen bg-surface font-body-md text-on-surface antialiased flex flex-col">
      {/* Header with Auth Capsule Trigger */}
      <Header
        goal={goal}
        targetCalories={targetCalories}
        onOpenAuth={() => setIsAuthModalOpen(true)}
      />

      {/* Navigation Tabs */}
      <TabNav activeTab={activeTab} setActiveTab={setActiveTab} />

      <main className="w-full max-w-7xl mx-auto px-margin-mobile md:px-margin-tablet lg:px-margin py-space-md flex-1">

        {/* Tab 1: Daily Meal Plan & Recipes */}
        {activeTab === "today" && (
          <MealPlanView
            mealPlanDisplayItems={activeMealItems}
            mealFrequency={mealFrequency}
            applyMealFrequency={applyMealFrequency}
            isSoloCook={isSoloCook}
            targetCalories={targetCalories}
            totalPlannedCals={totalPlannedCals}
            totalPlannedProt={totalPlannedProt}
            totalPlannedCarbs={totalPlannedCarbs}
            totalPlannedFat={totalPlannedFat}
            proteinGrams={macros.proteinGrams}
            carbsGrams={macros.carbsGrams}
            fatGrams={macros.fatGrams}
            totalPlannedFiber={totalPlannedFiber}
            onOpenRecipe={(recipe) => setActiveRecipeModal(recipe)}
            onSelectAlternative={handleSelectAlternative}
            onExplainWithAI={(foodId, foodName) => setExplainModal({ foodId, foodName })}
            onCookWithAI={(foodId, foodName) => setCookingModal({ foodId, foodName })}
            inStockPantryNames={inStockPantryNames}
            onGoToPantry={() => setActiveTab("pantry")}
            onRegenerateDay={refetchRecommendations}
            isLoadingRecommendations={recommendationsLoading}
            recommendationError={recommendationsError}
            onRetryRecommendations={refetchRecommendations}
            shuffleSlot={shuffleSlot}
            shufflingSlots={shufflingSlots}
          />
        )}

        {/* Tab 2: Real Progress & Adherence Analytics (Recharts) */}
        {activeTab === "progress" && <ProgressAnalytics />}

        {/* Tab 3: Grocery AI Scanner & Pantry */}
        {activeTab === "pantry" && (
          <div className="space-y-4">
            <PantryScanner
              pantryItems={pantryItems}
              togglePantryItem={togglePantryItem}
              onAddManualItem={handleAddManualPantryItem}
              onAddBatchItems={handleAddBatchPantryItems}
              onApplyToMealPlan={handleApplyPantryToMealPlan}
            />
            <PantryCookAssistant inStockPantryNames={inStockPantryNames} />
          </div>
        )}

        {/* Tab 4: Profile Studio, Routine & Biometrics */}
        {activeTab === "profile" && (
          <ProfileStudio
            isSoloCook={isSoloCook}
            setIsSoloCook={(val) => {
              setIsSoloCook(val);
              updateProfile({ is_solo_cook: val });
            }}
            mealFrequency={mealFrequency}
            applyMealFrequency={applyMealFrequency}
            activeSlots={activeSlots}
            toggleSlot={toggleSlot}
            weekdayBreakfastEffort={weekdayBreakfastEffort}
            setWeekdayBreakfastEffort={setWeekdayBreakfastEffort}
            weekdayLunchEffort={weekdayLunchEffort}
            setWeekdayLunchEffort={setWeekdayLunchEffort}
            goal={goal}
            setGoal={(g) => {
              setGoal(g);
              updateProfile({ goal: g });
            }}
            weight={weight}
            setWeight={(w) => {
              setWeight(w);
              updateProfile({ weight_kg: w });
            }}
            height={height}
            setHeight={(h) => {
              setHeight(h);
              updateProfile({ height_cm: h });
            }}
            age={age}
            setAge={(a) => {
              setAge(a);
              updateProfile({ age: a });
            }}
            gender={gender}
            setGender={(gen) => {
              setGender(gen);
              updateProfile({ gender: gen });
            }}
            activity={activity}
            setActivity={setActivity}
            bmr={bmr}
            tdee={tdee}
            targetCalories={targetCalories}
            adjText={adjText}
            carbsGrams={macros.carbsGrams}
            proteinGrams={macros.proteinGrams}
            fatGrams={macros.fatGrams}
          />
        )}

        {/* Tab 5: Mindful Swap Generator */}
        {activeTab === "swap" && <SwapView targetCalories={targetCalories} />}

        {/* Tab 6: Active Safety Shield */}
        {activeTab === "safety" && <SafetyShield />}

        {/* Tab 7: AI Meal Coach */}
        {activeTab === "ai" && (
          <div className="space-y-4">
            <AIAssistantView
              initialMealContext={askAIMealContext}
              onClearInitialContext={() => setAskAIMealContext(null)}
              availableFoods={activeMealItems.map((item) => ({
                id: item.recipe.id,
                name: item.recipe.name,
              }))}
            />
            <RecipeSuggestionView />
          </div>
        )}

        {/* Interactive Hinglish Recipe Modal */}
        <RecipeModal recipe={activeRecipeModal} onClose={() => setActiveRecipeModal(null)} />

        {/* AI Explanation Modal (Global Overlay) */}
        <AIExplanationModal
          isOpen={explainModal !== null}
          foodId={explainModal?.foodId ?? null}
          foodName={explainModal?.foodName ?? ""}
          onClose={() => setExplainModal(null)}
          onAskAboutMeal={(foodId, foodName) => {
            setAskAIMealContext({ id: foodId, name: foodName });
            setActiveTab("ai");
          }}
        />

        {/* AI Cooking Instructions Modal (Global Overlay) */}
        <CookingInstructionsModal
          isOpen={cookingModal !== null}
          foodId={cookingModal?.foodId ?? null}
          foodName={cookingModal?.foodName ?? ""}
          onClose={() => setCookingModal(null)}
        />

        {/* User Auth & Profile Modal */}
        <AuthModal isOpen={isAuthModalOpen} onClose={() => setIsAuthModalOpen(false)} />

        {/* Atmosphere Footer with Dataset Disclaimer */}
        <footer className="mt-12 pt-6 border-t border-surface-container-highest flex flex-col sm:flex-row items-center justify-between text-body-sm text-on-surface-variant font-light gap-2">
          <span>DietSense · Evidence-Based Nutrition · USDA &amp; ICMR-NIN verified</span>
          <span className="text-primary font-serif font-medium">
            Dataset estimates only. Not medical advice or diagnosis.
          </span>
        </footer>
      </main>

      {/* Global Auth Modal */}
      <AuthModal isOpen={isAuthModalOpen} onClose={() => setIsAuthModalOpen(false)} />
    </div>
  );
}

export default function HomePage() {
  return (
    <Suspense fallback={<div className="min-h-screen bg-[#faf7f2] flex items-center justify-center text-xs text-slate-500">Loading DietSense...</div>}>
      <MainApp />
    </Suspense>
  );
}
