"use client";

import { useState, useMemo, useEffect } from "react";
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
} from "@/lib/nutrition";
import { useAuth } from "@/context/AuthContext";

import { Header } from "@/components/Header";
import { TabNav, TabType } from "@/components/TabNav";
import { MealPlanView } from "@/components/MealPlanView";
import { PantryScanner } from "@/components/PantryScanner";
import { ProfileStudio } from "@/components/ProfileStudio";
import { SwapView } from "@/components/SwapView";
import { SafetyShield } from "@/components/SafetyShield";
import { RecipeModal } from "@/components/RecipeModal";
import { AuthModal } from "@/components/auth/AuthModal";

export default function HomePage() {
  const { user, updateProfile } = useAuth();
  const [activeTab, setActiveTab] = useState<TabType>("today");
  const [isAuthModalOpen, setIsAuthModalOpen] = useState<boolean>(false);

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

  // Recipe Modal State
  const [activeRecipeModal, setActiveRecipeModal] = useState<RecipeData | null>(null);

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
        pantryItems
      ),
    [activeSlots, targetCalories, macros, weekdayBreakfastEffort, weekdayLunchEffort, pantryItems]
  );

  const totalPlannedCals = mealPlanDisplayItems.reduce((acc, item) => acc + item.calories, 0);
  const totalPlannedProt = mealPlanDisplayItems.reduce((acc, item) => acc + item.protein, 0);
  const totalPlannedCarbs = mealPlanDisplayItems.reduce((acc, item) => acc + item.carbs, 0);
  const totalPlannedFat = mealPlanDisplayItems.reduce((acc, item) => acc + item.fat, 0);

  return (
    <main className="min-h-screen text-slate-800 p-3 sm:p-6 lg:p-10 flex flex-col items-center justify-start font-sans antialiased">
      <div className="relative w-full max-w-5xl overflow-hidden rounded-3xl border border-[#e8ded3]/80 bg-[#faf7f2]/95 backdrop-blur-xl p-5 sm:p-8 shadow-2xl text-slate-800 my-auto">
        
        {/* Header with Auth Capsule Trigger */}
        <Header
          goal={goal}
          targetCalories={targetCalories}
          onOpenAuth={() => setIsAuthModalOpen(true)}
        />

        {/* Navigation Tabs */}
        <TabNav activeTab={activeTab} setActiveTab={setActiveTab} />

        {/* Tab 1: Daily Meal Plan & Recipes */}
        {activeTab === "today" && (
          <MealPlanView
            mealPlanDisplayItems={mealPlanDisplayItems}
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
            onOpenRecipe={(recipe) => setActiveRecipeModal(recipe)}
          />
        )}

        {/* Tab 2: Grocery AI Scanner & Pantry */}
        {activeTab === "pantry" && (
          <PantryScanner
            pantryItems={pantryItems}
            togglePantryItem={togglePantryItem}
            onAddManualItem={handleAddManualPantryItem}
          />
        )}

        {/* Tab 3: Profile Studio, Routine & Biometrics */}
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

        {/* Tab 4: Mindful Swap Generator */}
        {activeTab === "swap" && <SwapView targetCalories={targetCalories} />}

        {/* Tab 5: Active Safety Shield */}
        {activeTab === "safety" && <SafetyShield />}

        {/* Interactive Hinglish Recipe Modal */}
        <RecipeModal recipe={activeRecipeModal} onClose={() => setActiveRecipeModal(null)} />

        {/* User Auth & Profile Modal */}
        <AuthModal isOpen={isAuthModalOpen} onClose={() => setIsAuthModalOpen(false)} />

        {/* Atmosphere Footer */}
        <div className="relative z-10 mt-6 pt-4 border-t border-[#e9dfd5] flex flex-col sm:flex-row items-center justify-between text-[11px] text-slate-500 font-light gap-2">
          <span>DietSense Atmos · Silk WebGL Shader Active</span>
          <span className="text-[#581825] font-serif font-medium">
            Every calorie is calculated, never hallucinated.
          </span>
        </div>
      </div>
    </main>
  );
}
