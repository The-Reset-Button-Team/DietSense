import React from "react";
import { RecipeData } from "@/types";
import { CalculatedMealItem } from "@/lib/nutrition";

interface MealCardProps {
  item: CalculatedMealItem;
  borderColor: string;
  onOpenRecipe: (recipe: RecipeData) => void;
}

export const MealCard: React.FC<MealCardProps> = ({ item, borderColor, onOpenRecipe }) => {
  return (
    <div
      className={`rounded-2xl bg-white p-4 sm:p-5 border border-[#e8ded3] flex flex-col md:flex-row md:items-center justify-between gap-4 border-l-4 ${borderColor} shadow-sm transition-all hover:shadow-md`}
    >
      <div className="flex items-start gap-3.5 flex-1">
        <div className="w-12 h-12 rounded-2xl bg-[#faf7f2] border border-[#e2d6c9] flex items-center justify-center text-2xl shrink-0 shadow-inner">
          {item.recipe.icon}
        </div>
        <div className="flex-1">
          <div className="flex items-center gap-2 flex-wrap">
            <span className="text-xs uppercase tracking-wider text-[#581825] font-bold">
              {item.recipe.slotLabel} · {item.recipe.timeSlot}
            </span>
            <span className="text-[10px] bg-[#eff6ff] text-[#1d4ed8] px-2 py-0.5 rounded-full border border-[#bfdbfe] font-semibold">
              {item.recipe.badge}
            </span>
            <span className="text-[10px] bg-[#fdf2f4] text-[#581825] px-2 py-0.5 rounded-full border border-[#fbcfe8] font-medium">
              {item.recipe.effortLevel === "low" ? "⚡ Quick Prep (<12m)" : "🍳 Moderate Prep (~25m)"}
            </span>
            {item.pantryStatus.isFullMatch ? (
              <span className="text-[10px] bg-emerald-50 text-emerald-700 px-2 py-0.5 rounded-full border border-emerald-200 font-bold flex items-center gap-1">
                <span>✨</span> 100% Samaan Available
              </span>
            ) : (
              <span className="text-[10px] bg-amber-50 text-amber-700 px-2 py-0.5 rounded-full border border-amber-200 font-medium">
                🛒 Missing: {item.pantryStatus.missing.join(", ")}
              </span>
            )}
          </div>

          <h3 className="text-base font-serif text-[#421018] mt-1 font-semibold">
            {item.recipe.name}
          </h3>
          <p className="text-xs text-slate-600 font-light mt-0.5 max-w-2xl">
            {item.recipe.tagline}
          </p>

          <div className="flex flex-wrap gap-2.5 sm:gap-3 text-xs text-slate-600 mt-2.5 font-medium items-center">
            <span className="text-[#421018] font-bold bg-[#f3eae0] px-2 py-0.5 rounded-md">
              🔥 {item.calories} kcal
            </span>
            <span>·</span>
            <span className="text-[#581825] font-semibold">💪 {item.protein}g Protein</span>
            <span>·</span>
            <span className="text-[#1d4ed8]">🌾 {item.carbs}g Carbs</span>
            <span>·</span>
            <span className="text-[#0369a1]">🥑 {item.fat}g Fat</span>
            <span>·</span>
            <span className="text-emerald-700">🌿 {item.fibre}g Fibre</span>
          </div>
        </div>
      </div>

      {/* Action Buttons */}
      <div className="flex sm:flex-col md:items-end justify-between sm:justify-center gap-2 shrink-0 pt-2 sm:pt-0 border-t sm:border-t-0 border-slate-100">
        <button
          onClick={() => onOpenRecipe(item.recipe)}
          className="px-3.5 py-2 rounded-xl bg-[#faf7f2] border border-[#d8c8b8] hover:bg-[#581825] hover:text-white text-[#581825] text-xs font-semibold transition-all shadow-sm flex items-center gap-1.5"
        >
          <span>📖</span> Hinglish Recipe &amp; Prep
        </button>
        <button className="px-3.5 py-1.5 rounded-xl bg-white border border-slate-200 hover:bg-slate-50 text-slate-600 text-xs font-medium transition-all">
          Mark Eaten ✓
        </button>
      </div>
    </div>
  );
};
