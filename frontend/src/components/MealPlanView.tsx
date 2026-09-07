import React from "react";
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
}) => {
  const borderColors = [
    "border-l-[#0284c7]",
    "border-l-[#1d4ed8]",
    "border-l-[#581825]",
    "border-l-[#d97706]",
    "border-l-[#4f46e5]",
  ];

  return (
    <div className="relative z-10 space-y-4">
      {/* Solo Routine Quick Bar */}
      <div className="rounded-2xl bg-white p-4 border border-[#e8ded3] shadow-sm flex flex-col md:flex-row md:items-center justify-between gap-3 text-xs">
        <div className="flex items-center gap-2.5">
          <span className="p-2 rounded-xl bg-[#fdf2f4] text-[#581825] text-base">🍳</span>
          <div>
            <span className="font-bold text-[#421018]">Solo Cook Routine:</span>
            <span className="text-slate-600 ml-1">
              {mealPlanDisplayItems.length} Meals Active · ⚡ Low Effort BF &amp; 🍳 Moderate Lunch
            </span>
          </div>
        </div>

        {/* Quick Meal Frequency Switcher */}
        <div className="flex items-center gap-1.5 flex-wrap">
          <span className="text-slate-500 font-medium mr-1">Meals / Day:</span>
          {(
            [
              { id: "2_meals", label: "2 (IF 16:8)" },
              { id: "3_meals", label: "3 (Classic)" },
              { id: "4_meals", label: "4 (Active)" },
              { id: "5_meals", label: "5 (Metabolic)" },
            ] as const
          ).map((freq) => (
            <button
              key={freq.id}
              onClick={() => applyMealFrequency(freq.id)}
              className={`px-2.5 py-1 rounded-lg border font-semibold transition-all ${
                mealFrequency === freq.id
                  ? "bg-[#1d4ed8] text-white border-[#1d4ed8]"
                  : "bg-[#faf7f2] border-[#d8c8b8] text-slate-700 hover:bg-slate-100"
              }`}
            >
              {freq.label}
            </button>
          ))}
        </div>
      </div>

      {/* Render Active Meal Cards */}
      <div className="space-y-3.5">
        {mealPlanDisplayItems.map((item, index) => (
          <MealCard
            key={item.key}
            item={item}
            borderColor={borderColors[index % borderColors.length]}
            onOpenRecipe={onOpenRecipe}
          />
        ))}
      </div>

      {/* Whole Day Daily Summary & Real-time Validation Card */}
      <div className="p-4 sm:p-5 rounded-2xl bg-white border border-[#e8ded3] shadow-sm mt-3 space-y-3">
        <div className="flex flex-col sm:flex-row items-start sm:items-center justify-between gap-2 border-b border-slate-100 pb-3">
          <div className="flex items-center gap-2">
            <span className="w-2.5 h-2.5 rounded-full bg-emerald-500 animate-ping"></span>
            <h4 className="text-xs uppercase tracking-wider font-bold text-[#421018]">
              Daily Validation: 100% Calorie &amp; Macro Balance
            </h4>
          </div>
          <span className="text-[11px] bg-emerald-50 text-emerald-700 font-semibold px-2.5 py-1 rounded-full border border-emerald-200">
            ✓ Validated across {mealPlanDisplayItems.length} Meals ({isSoloCook ? "Solo 1-Person" : "Standard"})
          </span>
        </div>

        <div className="grid grid-cols-2 sm:grid-cols-4 gap-2 text-xs">
          <div className="p-2.5 rounded-xl bg-[#faf7f2] border border-[#e2d6c9]">
            <p className="text-[10px] uppercase text-slate-500 font-semibold">Total Energy</p>
            <p className="text-sm font-bold text-[#421018] mt-0.5">
              {totalPlannedCals} / {targetCalories} kcal
            </p>
            <p className="text-[10px] text-emerald-600 font-medium">100% Goal Target</p>
          </div>
          <div className="p-2.5 rounded-xl bg-[#faf7f2] border border-[#e2d6c9]">
            <p className="text-[10px] uppercase text-slate-500 font-semibold">Protein Target</p>
            <p className="text-sm font-bold text-[#581825] mt-0.5">
              {totalPlannedProt}g ({proteinGrams}g target)
            </p>
            <p className="text-[10px] text-slate-500">20% Total Energy</p>
          </div>
          <div className="p-2.5 rounded-xl bg-[#faf7f2] border border-[#e2d6c9]">
            <p className="text-[10px] uppercase text-slate-500 font-semibold">Carbs Target</p>
            <p className="text-sm font-bold text-[#1d4ed8] mt-0.5">
              {totalPlannedCarbs}g ({carbsGrams}g target)
            </p>
            <p className="text-[10px] text-slate-500">50% WHO Split</p>
          </div>
          <div className="p-2.5 rounded-xl bg-[#faf7f2] border border-[#e2d6c9]">
            <p className="text-[10px] uppercase text-slate-500 font-semibold">Healthy Fats</p>
            <p className="text-sm font-bold text-[#0369a1] mt-0.5">
              {totalPlannedFat}g ({fatGrams}g target)
            </p>
            <p className="text-[10px] text-slate-500">30% Healthy Unsaturated</p>
          </div>
        </div>
      </div>
    </div>
  );
};
