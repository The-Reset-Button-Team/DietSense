"use client";

import React, { useState } from "react";
import { aiApi } from "@/lib/ai-client";
import { RecipeSuggestionResponse } from "@/types/ai";

interface RecipeSuggestionViewProps {
  availableFoods?: Array<{ id: number; name: string }>;
}

const MEAL_SLOTS = ["breakfast", "lunch", "dinner", "snack"] as const;
const CUISINES = ["Indian", "Pan-Asian", "Mediterranean", "Any"] as const;

export const RecipeSuggestionView: React.FC<RecipeSuggestionViewProps> = () => {
  const [loading, setLoading] = useState<boolean>(false);
  const [data, setData] = useState<RecipeSuggestionResponse | null>(null);
  const [error, setError] = useState<string | null>(null);

  const [slot, setSlot] = useState<string>("lunch");
  const [cuisine, setCuisine] = useState<string>("Indian");
  const [calorieTarget, setCalorieTarget] = useState<number>(500);

  const handleSuggest = async () => {
    setLoading(true);
    setError(null);

    try {
      const res = await aiApi.suggestRecipes({
        meal_slot: slot,
        target_calories: calorieTarget,
        cuisine: cuisine === "Any" ? undefined : cuisine,
      });
      setData(res);
    } catch (err: any) {
      setError(err?.message || "Failed to get recipe suggestions.");
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="rounded-3xl bg-white border border-[#e8ded3] p-5 sm:p-6 shadow-sm space-y-4">
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3 border-b border-slate-100 pb-3">
        <div>
          <div className="flex items-center gap-2">
            <span className="text-xs uppercase font-bold text-[#581825] tracking-wider flex items-center gap-1.5">
              <span>📋</span> AI Recipe Suggestions
            </span>
          </div>
          <h3 className="text-base font-serif font-bold text-[#421018] mt-0.5">
            Discover New Balanced Recipes
          </h3>
          <p className="text-xs text-slate-500">
            Get creative recipe ideas tailored to your calorie and cuisine preferences.
          </p>
        </div>
      </div>

      {/* Filters */}
      <div className="flex items-center gap-3 flex-wrap text-xs">
        <div className="flex items-center gap-1.5">
          <span className="text-slate-500 font-medium">Slot:</span>
          {MEAL_SLOTS.map((s) => (
            <button
              key={s}
              onClick={() => setSlot(s)}
              className={`px-2.5 py-1 rounded-lg border font-semibold transition-all capitalize ${
                slot === s
                  ? "bg-[#581825] text-white border-[#581825]"
                  : "bg-[#faf7f2] border-[#d8c8b8] text-slate-700 hover:bg-slate-100"
              }`}
            >
              {s}
            </button>
          ))}
        </div>

        <div className="flex items-center gap-1.5">
          <span className="text-slate-500 font-medium">Cuisine:</span>
          <select
            value={cuisine}
            onChange={(e) => setCuisine(e.target.value)}
            className="bg-[#faf7f2] border border-[#d8c8b8] rounded-xl px-2.5 py-1.5 text-xs text-slate-700"
          >
            {CUISINES.map((c) => (
              <option key={c} value={c}>{c}</option>
            ))}
          </select>
        </div>

        <div className="flex items-center gap-1.5">
          <span className="text-slate-500 font-medium">Target:</span>
          <input
            type="number"
            value={calorieTarget}
            onChange={(e) => setCalorieTarget(Number(e.target.value))}
            min={100}
            max={1500}
            step={50}
            className="w-20 bg-[#faf7f2] border border-[#d8c8b8] rounded-xl px-2 py-1.5 text-xs text-slate-700 text-center"
          />
          <span className="text-slate-500">kcal</span>
        </div>

        <button
          onClick={handleSuggest}
          disabled={loading}
          className="px-4 py-2 rounded-xl bg-[#581825] hover:bg-[#722230] text-white text-xs font-semibold shadow-sm transition-all disabled:opacity-50 flex items-center gap-1.5 shrink-0 ml-auto"
        >
          {loading ? (
            <>
              <span className="w-3.5 h-3.5 border-2 border-white border-t-transparent rounded-full animate-spin" />
              <span>Thinking...</span>
            </>
          ) : (
            <>
              <span>✨</span> Get Suggestions
            </>
          )}
        </button>
      </div>

      {/* Loading */}
      {loading && (
        <div className="py-8 flex flex-col items-center justify-center gap-2">
          <div className="w-6 h-6 border-2 border-[#581825] border-t-transparent rounded-full animate-spin" />
          <p className="text-xs text-slate-500 font-medium animate-pulse">
            Matching recipes from USDA database...
          </p>
        </div>
      )}

      {/* Error */}
      {!loading && error && (
        <div className="p-3.5 rounded-2xl bg-red-50 border border-red-200 text-red-800 text-xs flex items-center justify-between">
          <p>⚠️ {error}</p>
          <button
            onClick={handleSuggest}
            className="px-2.5 py-1 bg-red-800 text-white rounded-lg font-semibold hover:bg-red-900 text-[11px]"
          >
            Retry
          </button>
        </div>
      )}

      {/* Empty State */}
      {!loading && !data && !error && (
        <div className="py-6 px-4 bg-[#faf7f2] border border-dashed border-[#e2d6c9] rounded-2xl text-center text-xs text-slate-500 space-y-1">
          <p className="font-semibold text-slate-700">No suggestions yet</p>
          <p className="max-w-md mx-auto text-[11px] text-slate-500">
            Set your preferences above and click <strong>&quot;Get Suggestions&quot;</strong> to discover new balanced recipes.
          </p>
        </div>
      )}

      {/* Success */}
      {!loading && data && data.suggestions && (
        <div className="space-y-4">
          <div className="grid gap-3 sm:grid-cols-2">
            {data.suggestions.map((recipe, idx) => (
              <div
                key={idx}
                className="p-4 rounded-2xl bg-[#faf7f2] border border-[#e8ded3] flex flex-col justify-between space-y-3"
              >
                <div>
                  <div className="flex items-center justify-between gap-2">
                    <span className="text-[10px] bg-[#eff6ff] text-[#1d4ed8] px-2 py-0.5 rounded-full border border-[#bfdbfe] font-medium capitalize">
                      {recipe.meal_slot}
                    </span>
                    <span className="text-[10px] text-slate-400 font-mono">
                      USDA Anchored
                    </span>
                  </div>

                  <h4 className="text-sm font-serif font-bold text-[#421018] mt-1.5">
                    {recipe.title}
                  </h4>

                  <p className="text-[11px] text-slate-600 mt-1 leading-relaxed">
                    {recipe.overview}
                  </p>

                  {recipe.ingredients && recipe.ingredients.length > 0 && (
                    <div className="mt-2 text-[11px] text-slate-700">
                      <span className="font-bold text-[#581825]">Ingredients: </span>
                      {recipe.ingredients.join(" · ")}
                    </div>
                  )}
                </div>

                {/* Macro summary */}
                <div className="pt-2 border-t border-[#e2d6c9] flex items-center justify-between text-[11px] text-slate-600 font-medium">
                  <span className="text-[#421018] font-bold">
                    🔥 {recipe.verified_nutrition_estimate?.calories_kcal ?? 0} kcal
                  </span>
                  <span>💪 {recipe.verified_nutrition_estimate?.protein_g ?? 0}g Protein</span>
                  <span>🌾 {recipe.verified_nutrition_estimate?.carbohydrates_g ?? (recipe.verified_nutrition_estimate as any)?.carbs_g ?? 0}g Carbs</span>
                </div>
              </div>
            ))}
          </div>

          <p className="text-[10px] text-slate-400 italic text-center">
            {data.disclaimer}
          </p>
        </div>
      )}
    </div>
  );
};
