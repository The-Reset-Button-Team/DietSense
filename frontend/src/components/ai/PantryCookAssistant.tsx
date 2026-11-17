"use client";

import React, { useState } from "react";
import { aiApi } from "@/lib/ai-client";
import { PantryCookingResponse, PantryRecipeItem } from "@/types/ai";

interface PantryCookAssistantProps {
  inStockPantryNames: string[];
  onOpenCookingModal?: (recipe: PantryRecipeItem) => void;
}

export const PantryCookAssistant: React.FC<PantryCookAssistantProps> = ({
  inStockPantryNames,
}) => {
  const [loading, setLoading] = useState<boolean>(false);
  const [data, setData] = useState<PantryCookingResponse | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [prepTimeLimit, setPrepTimeLimit] = useState<number>(25);

  const generatePantryMeal = async () => {
    setLoading(true);
    setError(null);

    try {
      const res = await aiApi.pantryCook({
        custom_ingredients: inStockPantryNames,
        max_prep_time_mins: prepTimeLimit,
        meal_slot: "dinner",
      });
      setData(res);
    } catch (err: any) {
      setError(err?.message || "Failed to generate recipes from pantry items.");
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
              <span>🍳</span> AI Pantry Chef
            </span>
            <span className="text-[10px] bg-emerald-50 text-emerald-800 px-2 py-0.5 rounded-full border border-emerald-200 font-semibold">
              {inStockPantryNames.length} Items In-Stock
            </span>
          </div>
          <h3 className="text-base font-serif font-bold text-[#421018] mt-0.5">
            Cook With What You Have
          </h3>
          <p className="text-xs text-slate-500">
            Minimizes kitchen food waste using OCR-scanned grocery receipts and pantry inventory.
          </p>
        </div>

        <div className="flex items-center gap-2">
          <select
            value={prepTimeLimit}
            onChange={(e) => setPrepTimeLimit(Number(e.target.value))}
            className="text-xs bg-[#faf7f2] border border-[#d8c8b8] rounded-xl px-2.5 py-1.5 text-slate-700"
          >
            <option value={15}>⚡ Max 15 Mins</option>
            <option value={25}>🍳 Max 25 Mins</option>
            <option value={40}>🍲 Max 40 Mins</option>
          </select>

          <button
            onClick={generatePantryMeal}
            disabled={loading}
            className="px-4 py-2 rounded-xl bg-[#581825] hover:bg-[#722230] text-white text-xs font-semibold shadow-sm transition-all disabled:opacity-50 flex items-center gap-1.5 shrink-0"
          >
            {loading ? (
              <>
                <span className="w-3.5 h-3.5 border-2 border-white border-t-transparent rounded-full animate-spin" />
                <span>Cooking...</span>
              </>
            ) : (
              <>
                <span>✨</span> Generate Pantry Recipe
              </>
            )}
          </button>
        </div>
      </div>

      {/* Loading State */}
      {loading && (
        <div className="py-8 flex flex-col items-center justify-center gap-2">
          <div className="w-6 h-6 border-2 border-[#581825] border-t-transparent rounded-full animate-spin" />
          <p className="text-xs text-slate-500 font-medium animate-pulse">
            Matching scanned pantry items with USDA clinical catalog...
          </p>
        </div>
      )}

      {/* Error State */}
      {!loading && error && (
        <div className="p-3.5 rounded-2xl bg-red-50 border border-red-200 text-red-800 text-xs flex items-center justify-between">
          <p>⚠️ {error}</p>
          <button
            onClick={generatePantryMeal}
            className="px-2.5 py-1 bg-red-800 text-white rounded-lg font-semibold hover:bg-red-900 text-[11px]"
          >
            Retry
          </button>
        </div>
      )}

      {/* Empty State */}
      {!loading && !data && !error && (
        <div className="py-6 px-4 bg-[#faf7f2] border border-dashed border-[#e2d6c9] rounded-2xl text-center text-xs text-slate-500 space-y-1">
          <p className="font-semibold text-slate-700">No AI pantry recipe generated yet</p>
          <p className="max-w-md mx-auto text-[11px] text-slate-500">
            Click <strong>&quot;Generate Pantry Recipe&quot;</strong> to create a custom solo meal tailored to the{" "}
            {inStockPantryNames.length} ingredients currently in your kitchen.
          </p>
        </div>
      )}

      {/* Success State */}
      {!loading && data && data.recipes && (
        <div className="space-y-4">
          <div className="grid gap-3 sm:grid-cols-2">
            {data.recipes.map((recipe, idx) => (
              <div
                key={idx}
                className="p-4 rounded-2xl bg-[#faf7f2] border border-[#e8ded3] flex flex-col justify-between space-y-3"
              >
                <div>
                  <div className="flex items-center justify-between gap-2">
                    <span className="text-[10px] bg-amber-50 text-amber-800 px-2 py-0.5 rounded-full border border-amber-200 font-medium">
                      ⏱️ {recipe.prep_time_mins} mins prep
                    </span>
                    <span className="text-[10px] text-slate-400 font-mono">
                      USDA Anchored
                    </span>
                  </div>

                  <h4 className="text-sm font-serif font-bold text-[#421018] mt-1.5">
                    {recipe.recipe_name}
                  </h4>

                  {/* Matched Pantry Items */}
                  <div className="mt-2 text-[11px] space-y-1">
                    <p className="text-emerald-800 font-medium flex items-center gap-1">
                      <span>✓ Using In-Stock:</span> {recipe.matched_pantry_items.join(", ")}
                    </p>
                    {recipe.missing_items && recipe.missing_items.length > 0 && (
                      <p className="text-amber-800 font-medium flex items-center gap-1">
                        <span>🛒 Optional Missing:</span> {recipe.missing_items.join(", ")}
                      </p>
                    )}
                  </div>

                  {/* Cooking Steps Preview */}
                  <div className="mt-2.5 space-y-1 text-xs text-slate-700">
                    <span className="font-bold text-[#581825] text-[11px] block">Steps:</span>
                    <ol className="list-decimal pl-4 space-y-1 text-[11px]">
                      {recipe.cooking_steps.slice(0, 3).map((step, sIdx) => (
                        <li key={sIdx}>{step}</li>
                      ))}
                    </ol>
                  </div>
                </div>

                {/* Macro summary */}
                <div className="pt-2 border-t border-[#e2d6c9] flex items-center justify-between text-[11px] text-slate-600 font-medium">
                  <span className="text-[#421018] font-bold">
                    🔥 {recipe.nutrition_facts?.calories_kcal} kcal
                  </span>
                  <span>💪 {recipe.nutrition_facts?.protein_g}g Protein</span>
                  <span>🌾 {recipe.nutrition_facts?.carbohydrates_g}g Carbs</span>
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
