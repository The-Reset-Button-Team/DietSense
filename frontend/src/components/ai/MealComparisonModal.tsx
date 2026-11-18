"use client";

import React, { useState, useEffect, useCallback } from "react";
import { aiApi } from "@/lib/ai-client";
import { MealComparisonResponse } from "@/types/ai";

interface MealComparisonModalProps {
  isOpen: boolean;
  onClose: () => void;
  initialFoodIds?: number[];
  availableFoods?: Array<{ id: number; name: string }>;
}

const DEFAULT_FOODS = [
  { id: 1, name: "Vegetable Poha with Peanuts" },
  { id: 2, name: "Moong Dal & Oats Chilla" },
  { id: 3, name: "Brown Rice & Palak Dal Tadka" },
  { id: 5, name: "Foxtail Millet & Moong Dal Khichdi" },
  { id: 7, name: "Masala Paneer Bhurji with Whole Wheat Toast" },
];

export const MealComparisonModal: React.FC<MealComparisonModalProps> = ({
  isOpen,
  onClose,
  initialFoodIds = [1, 2],
  availableFoods = DEFAULT_FOODS,
}) => {
  const [selectedIds, setSelectedIds] = useState<number[]>(initialFoodIds.length >= 2 ? initialFoodIds : [1, 2]);
  const [priority, setPriority] = useState<string>("balanced");
  const [loading, setLoading] = useState<boolean>(false);
  const [data, setData] = useState<MealComparisonResponse | null>(null);
  const [error, setError] = useState<string | null>(null);

  const runComparison = useCallback(() => {
    if (selectedIds.length < 2) {
      setError("Please select at least 2 meals to compare.");
      return;
    }
    setLoading(true);
    setError(null);

    aiApi
      .compareMeals({ food_ids: selectedIds, preference_priority: priority })
      .then((res) => {
        setData(res);
        setLoading(false);
      })
      .catch((err) => {
        setError(err?.message || "Failed to compare meals.");
        setLoading(false);
      });
  }, [selectedIds, priority]);

  useEffect(() => {
    if (isOpen) {
      runComparison();
    }
  }, [isOpen, runComparison]);

  const toggleFoodSelection = (id: number) => {
    if (selectedIds.includes(id)) {
      if (selectedIds.length <= 2) {
        setError("You must select at least 2 meals.");
        return;
      }
      setSelectedIds(selectedIds.filter((x) => x !== id));
    } else {
      if (selectedIds.length >= 4) {
        setError("You can compare up to 4 meals at a time.");
        return;
      }
      setSelectedIds([...selectedIds, id]);
    }
  };

  if (!isOpen) return null;

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-3 sm:p-6 bg-black/60 backdrop-blur-sm animate-fadeIn">
      <div className="relative w-full max-w-3xl max-h-[90vh] overflow-y-auto rounded-3xl bg-[#faf7f2] border border-[#d8c8b8] p-5 sm:p-7 shadow-2xl text-slate-800 space-y-5">
        {/* Header */}
        <div className="flex items-start justify-between gap-4 border-b border-[#e9dfd5] pb-4">
          <div>
            <div className="flex items-center gap-2">
              <span className="text-xs uppercase font-bold text-[#581825] tracking-wider flex items-center gap-1.5">
                <span>⚖️</span> Objective Meal Comparison
              </span>
              <span className="text-[10px] bg-[#eff6ff] text-[#1d4ed8] px-2 py-0.5 rounded-full border border-[#bfdbfe] font-mono">
                {data?.source === "offline_fallback" ? "Evidence Engine" : "Gemini 3.8 Flash"}
              </span>
            </div>
            <h2 className="text-xl font-serif text-[#421018] font-bold mt-1">
              Side-by-Side Macronutrient Trade-offs
            </h2>
            <p className="text-xs text-slate-500">
              Evaluated strictly against USDA &amp; ICMR-NIN verified nutritional composition.
            </p>
          </div>

          <button
            onClick={onClose}
            className="w-8 h-8 rounded-full bg-white border border-[#d8c8b8] flex items-center justify-center text-slate-500 hover:text-black hover:bg-slate-100 transition-all font-bold shrink-0"
            aria-label="Close modal"
          >
            ✕
          </button>
        </div>

        {/* Meal Selector Chips */}
        <div className="space-y-1.5">
          <span className="text-[11px] font-bold text-slate-600 uppercase tracking-wide">
            Select 2 to 4 Meals:
          </span>
          <div className="flex flex-wrap gap-1.5">
            {availableFoods.map((f) => {
              const isSelected = selectedIds.includes(f.id);
              return (
                <button
                  key={f.id}
                  onClick={() => toggleFoodSelection(f.id)}
                  className={`px-3 py-1.5 rounded-xl border text-xs font-medium transition-all ${
                    isSelected
                      ? "bg-[#581825] text-white border-[#581825] shadow-xs"
                      : "bg-white border-[#d8c8b8] text-slate-700 hover:border-[#581825]"
                  }`}
                >
                  {isSelected ? "✓ " : "+ "}
                  {f.name}
                </button>
              );
            })}
          </div>
        </div>

        {/* Priority Filter */}
        <div className="flex items-center gap-2 flex-wrap text-xs">
          <span className="font-bold text-slate-600">Priority Goal:</span>
          {[
            { id: "balanced", label: "⚖️ Balanced" },
            { id: "protein", label: "💪 High Protein" },
            { id: "low_calorie", label: "🔥 Lowest Calorie" },
            { id: "fiber", label: "🌿 High Fiber" },
          ].map((p) => (
            <button
              key={p.id}
              onClick={() => setPriority(p.id)}
              className={`px-3 py-1.5 rounded-xl border font-medium transition-all ${
                priority === p.id
                  ? "bg-[#1d4ed8] text-white border-[#1d4ed8] shadow-xs"
                  : "bg-white border-[#d8c8b8] text-slate-600 hover:border-[#1d4ed8]"
              }`}
            >
              {p.label}
            </button>
          ))}
        </div>

        {/* Loading State */}
        {loading && (
          <div className="py-12 flex flex-col items-center justify-center gap-3">
            <div className="w-8 h-8 border-3 border-[#581825] border-t-transparent rounded-full animate-spin" />
            <p className="text-xs text-slate-500 font-medium animate-pulse">
              Computing side-by-side nutritional trade-offs...
            </p>
          </div>
        )}

        {/* Error State */}
        {!loading && error && (
          <div className="p-4 rounded-2xl bg-red-50 border border-red-200 text-red-800 text-xs space-y-1">
            <p className="font-semibold">⚠️ Comparison Notice</p>
            <p>{error}</p>
          </div>
        )}

        {/* Success State */}
        {!loading && data && (
          <div className="space-y-4">
            {/* Winner Badge */}
            {data.winner_for_goal && (
              <div className="p-3.5 rounded-2xl bg-emerald-50 border border-emerald-200 text-emerald-900 text-xs flex items-center justify-between gap-3">
                <div className="flex items-center gap-2">
                  <span className="text-lg">🏆</span>
                  <div>
                    <span className="font-bold">Recommended Winner for {priority.replace("_", " ")}:</span>{" "}
                    <span className="font-semibold underline text-emerald-950">{data.winner_for_goal}</span>
                  </div>
                </div>
              </div>
            )}

            {/* Side-by-Side Cards Grid */}
            <div className={`grid gap-3 ${data.compared_meals.length === 2 ? "grid-cols-1 sm:grid-cols-2" : "grid-cols-1 sm:grid-cols-3"}`}>
              {data.compared_meals.map((meal) => (
                <div
                  key={meal.id}
                  className={`p-3.5 rounded-2xl bg-white border ${
                    data.winner_for_goal === meal.name
                      ? "border-emerald-500 ring-2 ring-emerald-100"
                      : "border-[#e8ded3]"
                  } shadow-xs flex flex-col justify-between`}
                >
                  <div>
                    <span className="text-[10px] text-slate-400 font-mono uppercase tracking-wider">
                      {meal.food_category || "General"}
                    </span>
                    <h4 className="text-sm font-serif font-bold text-[#421018] mt-0.5">
                      {meal.name}
                    </h4>
                  </div>

                  <div className="mt-3 grid grid-cols-2 gap-1.5 text-center text-xs">
                    <div className="p-1.5 rounded-lg bg-[#faf7f2] border border-[#e2d6c9]">
                      <span className="text-[10px] text-slate-500 block">Calories</span>
                      <span className="font-bold text-[#421018]">{meal.calories_kcal} kcal</span>
                    </div>
                    <div className="p-1.5 rounded-lg bg-[#faf7f2] border border-[#e2d6c9]">
                      <span className="text-[10px] text-slate-500 block">Protein</span>
                      <span className="font-bold text-[#581825]">{meal.protein_g}g</span>
                    </div>
                    <div className="p-1.5 rounded-lg bg-[#faf7f2] border border-[#e2d6c9]">
                      <span className="text-[10px] text-slate-500 block">Carbs</span>
                      <span className="font-bold text-[#1d4ed8]">{meal.carbohydrates_g}g</span>
                    </div>
                    <div className="p-1.5 rounded-lg bg-[#faf7f2] border border-[#e2d6c9]">
                      <span className="text-[10px] text-slate-500 block">Fat</span>
                      <span className="font-bold text-[#0369a1]">{meal.fat_g}g</span>
                    </div>
                  </div>
                </div>
              ))}
            </div>

            {/* AI Narrative Analysis */}
            <div className="p-3.5 rounded-2xl bg-white border border-[#e8ded3] text-xs space-y-1.5">
              <span className="font-bold text-[#581825] uppercase tracking-wider block">
                Evidence-Based Analysis:
              </span>
              <p className="text-slate-700 leading-relaxed">
                {data.analysis}
              </p>
            </div>

            {/* Key Trade-offs */}
            {data.key_tradeoffs && data.key_tradeoffs.length > 0 && (
              <div className="p-3.5 rounded-2xl bg-[#eff6ff] border border-[#bfdbfe] text-xs space-y-1.5">
                <span className="font-bold text-[#1d4ed8] uppercase tracking-wide block">
                  Key Trade-Offs:
                </span>
                <ul className="space-y-1 text-slate-700">
                  {data.key_tradeoffs.map((t, idx) => (
                    <li key={idx} className="flex items-start gap-1.5">
                      <span className="text-[#1d4ed8] font-bold">•</span>
                      <span>{t}</span>
                    </li>
                  ))}
                </ul>
              </div>
            )}

            {/* Medical Disclaimer */}
            <p className="text-[10px] text-slate-400 italic text-center">
              {data.disclaimer}
            </p>
          </div>
        )}

        {/* Footer Actions */}
        <div className="pt-3 border-t border-[#e9dfd5] flex justify-end">
          <button
            onClick={onClose}
            className="px-4 py-2 rounded-xl bg-[#581825] hover:bg-[#722230] text-white text-xs font-semibold shadow-sm transition-all"
          >
            Close Comparison
          </button>
        </div>
      </div>
    </div>
  );
};
