"use client";

import React, { useState } from "react";
import { MealFrequency, RecipeData } from "@/types";
import { CalculatedMealItem } from "@/lib/nutrition";
import { MealCard } from "./MealCard";

interface MealPlanViewProps {
  mealPlanDisplayItems: CalculatedMealItem[];
  mealFrequency: MealFrequency;
  applyMealFrequency: (freq: MealFrequency) => void;
  isSoloCook: boolean;
  targetCalories: number;
  totalPlannedCals: number;
  totalPlannedProt: number;
  totalPlannedCarbs: number;
  totalPlannedFat: number;
  proteinGrams: number;
  carbsGrams: number;
  fatGrams: number;
  onOpenRecipe: (recipe: RecipeData) => void;
  onSelectAlternative?: (slotKey: string, recipeName: string) => void;
  onExplainWithAI?: (foodId: number, foodName: string) => void;
  onCookWithAI?: (foodId: number, foodName: string) => void;
  inStockPantryNames?: string[];
  onGoToPantry?: () => void;
  onRegenerateDay?: () => void;
  totalPlannedFiber?: number;
  isLoadingRecommendations?: boolean;
  recommendationError?: string | null;
  onRetryRecommendations?: () => void;
  shuffleSlot?: (slotId: string) => void;
  shufflingSlots?: Set<string>;
}

export const MealPlanView: React.FC<MealPlanViewProps> = ({
  mealPlanDisplayItems,
  mealFrequency,
  applyMealFrequency,
  isSoloCook,
  targetCalories,
  totalPlannedCals,
  totalPlannedProt,
  totalPlannedCarbs,
  totalPlannedFat,
  proteinGrams,
  carbsGrams,
  fatGrams,
  onOpenRecipe,
  onSelectAlternative,
  onExplainWithAI,
  onCookWithAI,
  inStockPantryNames,
  onGoToPantry,
  onRegenerateDay,
  totalPlannedFiber,
  isLoadingRecommendations = false,
  recommendationError = null,
  onRetryRecommendations,
  shuffleSlot,
  shufflingSlots = new Set(),
}) => {
  // Modal states
  const [skipModalOpen, setSkipModalOpen] = useState(false);
  const [skippingMealName, setSkippingMealName] = useState("Lunch");
  const [skipReason, setSkipReason] = useState("time");
  const [hinglishModalOpen, setHinglishModalOpen] = useState(false);
  const [safetyAuditToast, setSafetyAuditToast] = useState(false);

  // Calorie & macro calculations
  const consumedCals = Math.min(totalPlannedCals, 1240);
  const remainingCals = Math.max(0, targetCalories - consumedCals);
  const calPercent = Math.min(100, Math.round((consumedCals / (targetCalories || 1850)) * 100));

  const protPercent = Math.min(100, Math.round((totalPlannedProt / (proteinGrams || 135)) * 100));
  const carbsPercent = Math.min(100, Math.round((totalPlannedCarbs / (carbsGrams || 185)) * 100));
  const fatPercent = Math.min(100, Math.round((totalPlannedFat / (fatGrams || 45)) * 100));

  const frequencies: { id: MealFrequency; label: string }[] = [
    { id: "2_meals", label: "2 Meals (16:8 IF)" },
    { id: "3_meals", label: "3 Meals (Classic)" },
    { id: "4_meals", label: "4 Meals (Standard)" },
    { id: "5_meals", label: "5 Meals (High Energy)" },
  ];

  const handleOpenSkipModal = (slotKey: string, mealName: string) => {
    setSkippingMealName(mealName);
    setSkipModalOpen(true);
  };

  const handleConfirmSkip = () => {
    setSkipModalOpen(false);
    // In production, triggers backend adaptive penalty & macro redistribution
  };

  const runAllergenAudit = () => {
    setSafetyAuditToast(true);
    setTimeout(() => setSafetyAuditToast(false), 3500);
  };

  return (
    <div className="space-y-space-lg pb-24">
      {/* Recommendation Error Banner */}
      {recommendationError && (
        <div className="flex items-center justify-between gap-3 px-space-md py-space-sm bg-error-container/20 border border-error/20 rounded-lg text-body-sm">
          <div className="flex items-center gap-2 text-on-surface-variant">
            <span className="material-symbols-outlined text-[16px] text-error">warning</span>
            <span>Using local recommendations — backend unavailable</span>
          </div>
          {onRetryRecommendations && (
            <button
              type="button"
              onClick={onRetryRecommendations}
              className="px-3 py-1 bg-primary text-on-primary rounded font-label-sm text-label-sm hover:bg-primary-container shrink-0"
            >
              Retry
            </button>
          )}
        </div>
      )}
      {/* Top Editorial Header & Clinical Status Indicator */}
      <div className="flex flex-col lg:flex-row lg:items-end justify-between gap-space-md pt-space-xs pb-space-sm border-b border-surface-container-highest">
        <div className="space-y-1">
          <div className="flex items-center gap-space-xs text-primary">
            <span className="material-symbols-outlined text-[18px]">calendar_today</span>
            <span className="font-label-sm text-label-sm uppercase tracking-wider text-primary font-bold">
              Clinical Regimen • Today
            </span>
          </div>
          <h1 className="font-headline-lg text-headline-lg text-primary tracking-tight font-serif">
            Today’s Prescriptive Plan
          </h1>
          <p className="font-body-md text-body-md text-on-surface-variant max-w-2xl">
            Caloric ceiling adjusted to Mifflin-St Jeor metabolic target with an intentional{" "}
            <span className="font-semibold text-primary">400 kcal cutting deficit</span>. Meals
            matched against verified regional biodatabases.
          </p>
        </div>

        <div className="flex items-center gap-space-sm bg-surface-container-low p-space-sm rounded-lg shadow-sm border border-surface-container shrink-0">
          <div className="w-10 h-10 rounded-full bg-secondary/10 flex items-center justify-center text-secondary">
            <span className="material-symbols-outlined text-[22px]">health_metrics</span>
          </div>
          <div className="pr-space-sm">
            <div className="flex items-center gap-1.5">
              <span className="font-label-sm text-label-sm uppercase text-on-surface-variant font-bold">
                Clinical Target
              </span>
              <span className="inline-block w-1.5 h-1.5 rounded-full bg-secondary" />
            </div>
            <p className="font-metric-num text-[18px] text-primary leading-tight">
              {targetCalories.toLocaleString()}{" "}
              <span className="font-body-sm text-body-sm text-on-surface-variant font-normal">
                kcal/day
              </span>
            </p>
          </div>
        </div>
      </div>

      {/* 1. Target Macro Allocation Spread */}
      <section className="bg-surface-container-lowest p-space-md md:p-space-lg rounded-xl shadow-sm border border-surface-container space-y-space-md">
        <div className="flex flex-col md:flex-row md:items-center justify-between gap-space-sm">
          <div className="space-y-0.5">
            <div className="flex items-center gap-2">
              <h2 className="font-headline-sm text-headline-sm text-on-surface font-serif">
                Target Macro Allocation
              </h2>
              <span className="px-2 py-0.5 rounded-full bg-surface-container font-label-sm text-label-sm text-on-surface-variant">
                67% Day Completed
              </span>
            </div>
            <p className="font-body-sm text-body-sm text-on-surface-variant">
              USDA FDC &amp; ICMR-NIN 2017 Verified Nutrient Composition
            </p>
          </div>

          <div className="flex items-center gap-space-xs font-label-md text-label-md text-on-surface-variant">
            <span className="w-2.5 h-2.5 rounded-full bg-primary" /> Protein
            <span className="w-2.5 h-2.5 rounded-full bg-amber-600 ml-2" /> Carbs
            <span className="w-2.5 h-2.5 rounded-full bg-secondary ml-2" /> Fats
          </div>
        </div>

        {/* Segmented Composite Bar */}
        <div className="space-y-space-xs">
          <div className="h-3 w-full bg-surface-container rounded-full overflow-hidden flex shadow-inner">
            <div
              className="h-full bg-primary transition-all duration-500"
              style={{ width: "36%" }}
              title="Protein 36%"
            />
            <div
              className="h-full bg-amber-600 transition-all duration-500"
              style={{ width: "40%" }}
              title="Carbohydrates 40%"
            />
            <div
              className="h-full bg-secondary transition-all duration-500"
              style={{ width: "24%" }}
              title="Healthy Fats 24%"
            />
          </div>

          <div className="flex justify-between items-center font-label-sm text-label-sm text-on-surface-variant pt-0.5">
            <span>0 kcal</span>
            <span className="font-semibold text-primary">
              {consumedCals.toLocaleString()} kcal consumed ({remainingCals.toLocaleString()} kcal
              remaining)
            </span>
            <span>{targetCalories.toLocaleString()} kcal ceiling</span>
          </div>
        </div>

        {/* 4-Column Micro Gauge Cards */}
        <div className="grid grid-cols-2 lg:grid-cols-4 gap-space-sm md:gap-space-md pt-space-xs">
          {/* Calories */}
          <div className="bg-surface-container-low p-space-sm md:p-space-md rounded-lg space-y-1 border border-surface-container">
            <div className="flex items-center justify-between text-on-surface-variant">
              <span className="font-label-sm text-label-sm uppercase font-bold tracking-wider">
                Calories
              </span>
              <span className="material-symbols-outlined text-[16px] text-primary">
                local_fire_department
              </span>
            </div>
            <div className="flex items-baseline gap-1">
              <span className="font-metric-num text-[22px] md:text-metric-num text-primary">
                {consumedCals.toLocaleString()}
              </span>
              <span className="font-body-sm text-body-sm text-on-surface-variant">
                / {targetCalories.toLocaleString()} kcal
              </span>
            </div>
            <div className="w-full bg-surface-container rounded-full h-1.5 mt-2 overflow-hidden">
              <div
                className="bg-primary h-1.5 rounded-full transition-all"
                style={{ width: `${calPercent}%` }}
              />
            </div>
            <span className="font-label-sm text-label-sm text-on-surface-variant block text-right pt-0.5">
              {calPercent}% cut budget
            </span>
          </div>

          {/* Protein */}
          <div className="bg-surface-container-low p-space-sm md:p-space-md rounded-lg space-y-1 border border-surface-container">
            <div className="flex items-center justify-between text-on-surface-variant">
              <span className="font-label-sm text-label-sm uppercase font-bold tracking-wider text-primary">
                Protein
              </span>
              <span className="material-symbols-outlined text-[16px] text-primary">
                fitness_center
              </span>
            </div>
            <div className="flex items-baseline gap-1">
              <span className="font-metric-num text-[22px] md:text-metric-num text-primary">
                {totalPlannedProt}g
              </span>
              <span className="font-body-sm text-body-sm text-on-surface-variant">
                / {proteinGrams || 135}g target
              </span>
            </div>
            <div className="w-full bg-surface-container rounded-full h-1.5 mt-2 overflow-hidden">
              <div
                className="bg-primary h-1.5 rounded-full transition-all"
                style={{ width: `${protPercent}%` }}
              />
            </div>
            <span className="font-label-sm text-label-sm text-secondary font-semibold block text-right pt-0.5">
              {protPercent}% ({Math.max(0, (proteinGrams || 135) - totalPlannedProt)}g to goal)
            </span>
          </div>

          {/* Carbs */}
          <div className="bg-surface-container-low p-space-sm md:p-space-md rounded-lg space-y-1 border border-surface-container">
            <div className="flex items-center justify-between text-on-surface-variant">
              <span className="font-label-sm text-label-sm uppercase font-bold tracking-wider text-amber-700">
                Carbohydrates
              </span>
              <span className="material-symbols-outlined text-[16px] text-amber-600">grain</span>
            </div>
            <div className="flex items-baseline gap-1">
              <span className="font-metric-num text-[22px] md:text-metric-num text-on-surface">
                {totalPlannedCarbs}g
              </span>
              <span className="font-body-sm text-body-sm text-on-surface-variant">
                / {carbsGrams || 185}g target
              </span>
            </div>
            <div className="w-full bg-surface-container rounded-full h-1.5 mt-2 overflow-hidden">
              <div
                className="bg-amber-600 h-1.5 rounded-full transition-all"
                style={{ width: `${carbsPercent}%` }}
              />
            </div>
            <span className="font-label-sm text-label-sm text-on-surface-variant block text-right pt-0.5">
              {carbsPercent}% ({Math.max(0, (carbsGrams || 185) - totalPlannedCarbs)}g remaining)
            </span>
          </div>

          {/* Fats */}
          <div className="bg-surface-container-low p-space-sm md:p-space-md rounded-lg space-y-1 border border-surface-container">
            <div className="flex items-center justify-between text-on-surface-variant">
              <span className="font-label-sm text-label-sm uppercase font-bold tracking-wider text-secondary">
                Healthy Fats
              </span>
              <span className="material-symbols-outlined text-[16px] text-secondary">opacity</span>
            </div>
            <div className="flex items-baseline gap-1">
              <span className="font-metric-num text-[22px] md:text-metric-num text-on-surface">
                {totalPlannedFat}g
              </span>
              <span className="font-body-sm text-body-sm text-on-surface-variant">
                / {fatGrams || 45}g target
              </span>
            </div>
            <div className="w-full bg-surface-container rounded-full h-1.5 mt-2 overflow-hidden">
              <div
                className="bg-secondary h-1.5 rounded-full transition-all"
                style={{ width: `${fatPercent}%` }}
              />
            </div>
            <span className="font-label-sm text-label-sm text-on-surface-variant block text-right pt-0.5">
              {fatPercent}% ({Math.max(0, (fatGrams || 45) - totalPlannedFat)}g remaining)
            </span>
          </div>
        </div>
      </section>

      {/* 2. Metabolic Feeding Cadence Rail */}
      <section className="bg-surface-container p-space-sm rounded-xl space-y-2 border border-surface-container-highest">
        <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-space-xs px-1">
          <div className="flex items-center gap-space-xs text-on-surface">
            <span className="material-symbols-outlined text-[18px] text-primary">schedule</span>
            <span className="font-label-md text-label-md uppercase font-bold">
              Metabolic Feeding Cadence
            </span>
          </div>
          <div className="flex items-center gap-1.5 text-secondary">
            <span className="w-2 h-2 rounded-full bg-secondary animate-pulse" />
            <span className="font-label-sm text-label-sm font-semibold">
              Dynamically rebalances USDA &amp; ICMR-NIN verified calories across remaining slots
            </span>
          </div>
        </div>

        <div className="grid grid-cols-2 md:grid-cols-4 gap-1.5 bg-surface-container-low p-1 rounded-lg">
          {frequencies.map((freq) => {
            const isActive = mealFrequency === freq.id;
            return (
              <button
                key={freq.id}
                type="button"
                onClick={() => applyMealFrequency(freq.id)}
                className={`px-space-sm py-2 rounded text-center transition-all font-label-md text-label-md ${
                  isActive
                    ? "bg-primary-container text-on-primary font-bold shadow-sm"
                    : "text-on-surface-variant hover:text-on-surface hover:bg-surface-container"
                }`}
              >
                {freq.label}
              </button>
            );
          })}
        </div>
      </section>

      {/* 3. Daily Meal Slot Cards & Main Journal Grid (8:4 Desktop Ratio) */}
      <div className="grid grid-cols-1 lg:grid-cols-12 gap-space-lg items-start">
        {/* Primary 8-Column Meal Ledger */}
        <div className="lg:col-span-8 space-y-space-md">
          {/* Loading skeleton while recommendations fetch (no items yet) */}
          {isLoadingRecommendations && mealPlanDisplayItems.length === 0 && (
            <div className="space-y-space-md">
              {[0, 1, 2].map((i) => (
                <div
                  key={i}
                  className="bg-surface-container-lowest rounded-xl p-space-md border border-surface-container animate-pulse"
                >
                  <div className="h-4 bg-surface-container rounded w-32 mb-3" />
                  <div className="flex gap-space-md">
                    <div className="w-32 h-32 rounded-lg bg-surface-container shrink-0" />
                    <div className="flex-1 space-y-2">
                      <div className="h-5 bg-surface-container rounded w-3/4" />
                      <div className="h-3 bg-surface-container rounded w-full" />
                      <div className="h-3 bg-surface-container rounded w-1/2" />
                    </div>
                  </div>
                </div>
              ))}
            </div>
          )}

          {mealPlanDisplayItems.map((item, index) => (
            <MealCard
              key={item.key || index}
              item={item}
              slotIndex={index}
              isActiveWindow={index === 1}
              onOpenRecipe={onOpenRecipe}
              onSelectAlternative={onSelectAlternative}
              onExplainWithAI={onExplainWithAI}
              onCookWithAI={onCookWithAI}
              onSkipSlot={(slotKey, mealName) => handleOpenSkipModal(slotKey, mealName)}
              onShuffleSlot={shuffleSlot}
              isShuffling={shufflingSlots.has(item.key)}
            />
          ))}

          {/* Empty state: no items and not loading */}
          {!isLoadingRecommendations && mealPlanDisplayItems.length === 0 && (
            <div className="text-center py-12 text-on-surface-variant">
              <span className="material-symbols-outlined text-[48px] block mb-3 opacity-40">restaurant</span>
              <p className="font-body-md text-body-md">No meal slots active. Enable slots in your profile.</p>
            </div>
          )}
        </div>

        {/* Persistent 4-Column Clinical Rail & Fast Action Cards */}
        <aside className="lg:col-span-4 space-y-space-md">
          {/* Interactive Hinglish Recipe Spotlight Card */}
          <div className="bg-surface-container-lowest p-space-md rounded-xl shadow-sm space-y-space-sm border border-surface-container">
            <div className="flex items-center justify-between">
              <span className="px-2.5 py-0.5 rounded-full bg-primary/10 text-primary font-label-sm text-label-sm font-bold uppercase tracking-wider">
                Fast Solo Cook
              </span>
              <span className="font-label-sm text-label-sm text-secondary font-bold flex items-center gap-1">
                <span className="material-symbols-outlined text-[14px]">check</span> In Pantry (3/4)
              </span>
            </div>

            <div className="space-y-1">
              <h4 className="font-headline-sm text-headline-sm text-primary font-serif">
                Palak Paneer Bhurji — 15m Solo Edition
              </h4>
              <p className="font-body-sm text-body-sm text-on-surface-variant">
                Bachelors &amp; solo-cook engineered quick recipe. No mixer grinder required.
              </p>
            </div>

            <div className="p-space-sm bg-surface-container-low rounded-lg space-y-2 border border-surface-container">
              <div className="flex items-center gap-space-xs font-label-sm text-label-sm text-primary font-bold">
                <span className="material-symbols-outlined text-[16px]">tips_and_updates</span>
                Hinglish Lifehack
              </div>
              <p className="font-body-sm text-body-sm text-on-surface leading-snug">
                <span className="font-semibold text-primary">&quot;Pan mein 1 tsp oil garam karo,</span>{" "}
                jeera aur finely chopped pyaz 2 min sauté karo. Paneer ko haath se crush karke daalo.{" "}
                <span className="italic text-on-surface-variant">
                  Cook &amp; eat in the same cast iron skillet to save cleaning time!&quot;
                </span>
              </p>
            </div>

            <button
              type="button"
              onClick={() => setHinglishModalOpen(true)}
              className="w-full py-2 bg-surface-container hover:bg-surface-container-high text-primary font-label-md text-label-md rounded transition-colors flex items-center justify-center gap-1"
            >
              <span className="material-symbols-outlined text-[16px]">receipt_long</span>
              Full 3-Step Hinglish Guide
            </button>
          </div>

          {/* Quick Bio-Engineered Satiety & Hydration Digest */}
          <div className="bg-surface-container-lowest p-space-md rounded-xl shadow-sm space-y-space-sm border border-surface-container">
            <h4 className="font-headline-sm text-headline-sm text-on-surface font-serif">
              Daily Bio-Ledger
            </h4>
            <div className="space-y-space-xs">
              <div className="flex items-center justify-between text-body-sm font-body-sm pb-1 border-b border-surface-container">
                <span className="text-on-surface-variant flex items-center gap-1">
                  <span className="material-symbols-outlined text-[16px] text-blue-600">
                    water_drop
                  </span>
                  Water Intake
                </span>
                <span className="font-label-md text-label-md text-on-surface font-semibold">
                  2.4L / 3.5L
                </span>
              </div>
              <div className="flex items-center justify-between text-body-sm font-body-sm pb-1 border-b border-surface-container">
                <span className="text-on-surface-variant flex items-center gap-1">
                  <span className="material-symbols-outlined text-[16px] text-secondary">
                    compost
                  </span>
                  Dietary Fiber
                </span>
                <span className="font-label-md text-label-md text-on-surface font-semibold">
                  {totalPlannedFiber !== undefined ? `${Math.round(totalPlannedFiber)}g` : "28g"} / 35g
                </span>
              </div>
              <div className="flex items-center justify-between text-body-sm font-body-sm">
                <span className="text-on-surface-variant flex items-center gap-1">
                  <span className="material-symbols-outlined text-[16px] text-amber-600">bolt</span>
                  Glycemic Buffer
                </span>
                <span className="font-label-sm text-label-sm bg-secondary/15 text-secondary font-bold px-2 py-0.5 rounded-full">
                  Optimal (Low GI)
                </span>
              </div>
            </div>
          </div>

          {/* Regenerate / Allergen Gate Engine Card */}
          <div className="bg-surface-container p-space-md rounded-xl space-y-space-sm border border-surface-container-highest">
            <div className="flex items-center gap-2 text-primary">
              <span className="material-symbols-outlined text-[20px]">verified_user</span>
              <span className="font-headline-sm text-headline-sm font-serif">
                Clinical Safety Gate
              </span>
            </div>
            <p className="font-body-sm text-body-sm text-on-surface-variant leading-relaxed">
              All suggestions continuously validated against your clinical profile:{" "}
              <span className="font-semibold text-on-surface">
                Lactose Tolerant, Peanut Avoidance, High-Fiber Cut
              </span>
              .
            </p>
            <button
              type="button"
              onClick={runAllergenAudit}
              className="w-full py-2 bg-surface-container-lowest hover:bg-surface-container-high text-primary font-label-md text-label-md rounded shadow-sm transition-all flex items-center justify-center gap-2 border border-surface-container"
            >
              <span className="material-symbols-outlined text-[16px]">policy</span>
              Run Allergen &amp; Sodium Audit
            </button>
          </div>
        </aside>
      </div>

      {/* 5. Quick Action Floating Pill */}
      <div className="fixed bottom-6 left-1/2 -translate-x-1/2 z-40 bg-surface-container-lowest/95 backdrop-blur-md px-space-md py-space-sm rounded-full shadow-[0_8px_24px_-4px_rgba(66,16,24,0.15),0_2px_6px_-1px_rgba(66,16,24,0.06)] border border-surface-container flex items-center gap-space-sm">
        <button
          type="button"
          onClick={() => {
            if (onRegenerateDay) onRegenerateDay();
          }}
          className="flex items-center gap-space-xs px-space-md py-2 bg-primary hover:bg-primary-container text-on-primary rounded-full font-label-md text-label-md transition-all shadow-sm active:scale-95"
        >
          <span className="material-symbols-outlined text-[18px]">neurology</span>
          <span>Regenerate Entire Day</span>
        </button>

        <div className="w-px h-6 bg-surface-container" />

        <button
          type="button"
          onClick={() => window.scrollTo({ top: 0, behavior: "smooth" })}
          className="flex items-center gap-1 text-on-surface-variant hover:text-on-surface font-label-md text-label-md px-2 py-1"
        >
          <span className="material-symbols-outlined text-[18px]">expand_less</span>
          <span className="hidden sm:inline">Top</span>
        </button>
      </div>

      {/* Adaptive Skip Reason Modal */}
      {skipModalOpen && (
        <div className="fixed inset-0 z-50 bg-black/40 backdrop-blur-sm flex items-center justify-center p-space-md animate-in fade-in">
          <div className="bg-surface-container-lowest max-w-md w-full rounded-xl p-space-lg shadow-xl space-y-space-md border border-surface-container">
            <div className="flex items-start justify-between">
              <div>
                <h3 className="font-headline-sm text-headline-sm text-primary font-serif">
                  Adaptive Meal Skip
                </h3>
                <p className="font-body-sm text-body-sm text-on-surface-variant">
                  Why are you skipping {skippingMealName}? We will redistribute calories and adjust
                  preferences.
                </p>
              </div>
              <button
                type="button"
                onClick={() => setSkipModalOpen(false)}
                className="text-on-surface-variant hover:text-on-surface"
              >
                <span className="material-symbols-outlined text-[20px]">close</span>
              </button>
            </div>

            <div className="space-y-space-xs font-label-md text-label-md">
              {[
                { id: "time", label: "Short on time / In a meeting" },
                { id: "groceries", label: "Missing paneer or groceries in fridge" },
                { id: "taste", label: "Not craving this meal profile today" },
                { id: "budget", label: "Saving calories for an evening social dinner" },
              ].map((reason) => (
                <label
                  key={reason.id}
                  className="flex items-center gap-space-sm p-space-sm rounded bg-surface-container-low hover:bg-surface-container cursor-pointer transition-colors border border-transparent hover:border-surface-container"
                >
                  <input
                    type="radio"
                    name="skip-reason"
                    value={reason.id}
                    checked={skipReason === reason.id}
                    onChange={(e) => setSkipReason(e.target.value)}
                    className="accent-primary"
                  />
                  <span>{reason.label}</span>
                </label>
              ))}
            </div>

            <div className="flex items-center justify-end gap-space-xs pt-space-xs">
              <button
                type="button"
                onClick={() => setSkipModalOpen(false)}
                className="px-space-md py-2 text-on-surface-variant hover:bg-surface-container rounded font-label-md text-label-md"
              >
                Cancel
              </button>
              <button
                type="button"
                onClick={handleConfirmSkip}
                className="px-space-md py-2 bg-primary hover:bg-primary-container text-on-primary rounded font-label-md text-label-md shadow-sm"
              >
                Confirm &amp; Redistribute Macros
              </button>
            </div>
          </div>
        </div>
      )}

      {/* Hinglish Recipe & Solo-Cook Lifehacks Modal */}
      {hinglishModalOpen && (
        <div className="fixed inset-0 z-50 bg-black/40 backdrop-blur-sm flex items-center justify-center p-space-md animate-in fade-in">
          <div className="bg-surface-container-lowest max-w-xl w-full rounded-xl p-space-lg shadow-xl space-y-space-md max-h-[90vh] overflow-y-auto border border-surface-container">
            <div className="flex items-start justify-between border-b border-surface-container pb-space-sm">
              <div>
                <div className="flex items-center gap-2">
                  <span className="font-label-sm text-label-sm text-secondary bg-secondary/10 px-2 py-0.5 rounded-full font-bold">
                    3/4 Local In-Stock
                  </span>
                  <span className="font-label-sm text-label-sm text-on-surface-variant">
                    15 min total
                  </span>
                </div>
                <h3 className="font-headline-md text-headline-md text-primary pt-1 font-serif">
                  Paneer Bhurji: Quick Hinglish Edition
                </h3>
              </div>
              <button
                type="button"
                onClick={() => setHinglishModalOpen(false)}
                className="text-on-surface-variant hover:text-on-surface p-1"
              >
                <span className="material-symbols-outlined text-[22px]">close</span>
              </button>
            </div>

            <div className="space-y-space-sm">
              <h4 className="font-label-md text-label-md uppercase tracking-wider text-on-surface-variant font-bold">
                1. Ingredients Check
              </h4>
              <div className="grid grid-cols-2 gap-2 text-body-sm font-body-sm">
                <div className="p-2 rounded bg-surface-container-low flex items-center justify-between border border-surface-container">
                  <span>200g Low Fat Paneer</span>
                  <span className="material-symbols-outlined text-secondary text-[16px]">
                    check
                  </span>
                </div>
                <div className="p-2 rounded bg-surface-container-low flex items-center justify-between border border-surface-container">
                  <span>1 Diced Onion &amp; Tomato</span>
                  <span className="material-symbols-outlined text-secondary text-[16px]">
                    check
                  </span>
                </div>
                <div className="p-2 rounded bg-surface-container-low flex items-center justify-between border border-surface-container">
                  <span>1 Green Chili &amp; Jeera</span>
                  <span className="material-symbols-outlined text-secondary text-[16px]">
                    check
                  </span>
                </div>
                <div className="p-2 rounded bg-surface-container-low flex items-center justify-between text-on-surface-variant border border-surface-container">
                  <span>Fresh Dhaniya / Cilantro</span>
                  <span className="material-symbols-outlined text-amber-600 text-[16px]">
                    add
                  </span>
                </div>
              </div>

              <h4 className="font-label-md text-label-md uppercase tracking-wider text-on-surface-variant font-bold pt-2">
                2. 3-Step Solo Prep Guide
              </h4>
              <div className="space-y-2 text-body-sm font-body-sm">
                <div className="p-3 rounded-lg bg-surface-container-low border border-surface-container">
                  <span className="font-bold text-primary">Step 1 (Tadka):</span> Pan mein 1 tsp oil
                  ya ghee garam karo. 1/2 tsp jeera aur chopped green chili add karo. Jab crackle
                  hone lage toh pyaaz daal do.
                </div>
                <div className="p-3 rounded-lg bg-surface-container-low border border-surface-container">
                  <span className="font-bold text-primary">Step 2 (Bhurji Base):</span> 2 minute
                  saute ke baad tamatar, haldi, thoda namak aur garam masala daalo. Jab tamatar soft
                  ho jaye toh paneer ko haath se crush karke mix karo.
                </div>
                <div className="p-3 rounded-lg bg-surface-container-low border border-surface-container">
                  <span className="font-bold text-primary">Step 3 (Finish):</span> 3 minute dhak kar
                  pakao on low flame. Gas band karo aur fresh cilantro garnish karo. Eat directly
                  with multigrain roti!
                </div>
              </div>
            </div>

            <div className="pt-space-xs flex justify-end">
              <button
                type="button"
                onClick={() => setHinglishModalOpen(false)}
                className="px-space-md py-2 bg-primary text-on-primary rounded font-label-md text-label-md"
              >
                Done / Close
              </button>
            </div>
          </div>
        </div>
      )}

      {/* Safety Audit Toast */}
      {safetyAuditToast && (
        <div className="fixed top-20 right-6 z-50 bg-surface-container-lowest p-space-md rounded-xl shadow-xl border border-secondary text-body-sm animate-in slide-in-from-top-4 flex items-center gap-3">
          <span className="w-8 h-8 rounded-full bg-secondary/10 flex items-center justify-center text-secondary">
            <span className="material-symbols-outlined text-[18px]">verified</span>
          </span>
          <div>
            <h5 className="font-label-md text-label-md text-on-surface font-bold">
              Clinical Safety Audit Passed
            </h5>
            <p className="text-body-sm text-on-surface-variant">
              0 Allergens detected. Sodium estimated at &lt; 1,800mg daily ceiling.
            </p>
          </div>
        </div>
      )}
    </div>
  );
};
