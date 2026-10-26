import React, { useState } from "react";
import { RecipeData } from "@/types";
import { CalculatedMealItem } from "@/lib/nutrition";

interface MealCardProps {
  item: CalculatedMealItem;
  borderColor: string;
  onOpenRecipe: (recipe: RecipeData) => void;
  onSelectAlternative?: (slotKey: string, recipeName: string) => void;
  reason?: string;
}

export const MealCard: React.FC<MealCardProps> = ({
  item,
  borderColor,
  onOpenRecipe,
  onSelectAlternative,
  reason,
}) => {
  const [loggedStatus, setLoggedStatus] = useState<string | null>(null);
  const [showSwapModal, setShowSwapModal] = useState<boolean>(false);

  // Generate default explainability string from meal factors if not supplied
  const displayReason =
    reason ||
    (item.pantryStatus.isFullMatch
      ? `✨ Recommended: 100% matched to your scanned grocery bill (${item.pantryStatus.matched?.join(", ")}). Saves prep time and avoids waste!`
      : item.pantryStatus.matched && item.pantryStatus.matched.length > 0
      ? `✨ Pantry Match: Uses ${item.pantryStatus.matched.length} scanned ingredients from your kitchen (${item.pantryStatus.matched.join(", ")}).`
      : `Recommended because it matches your calorie target well (${item.calories} kcal), fits your budget, and ~${item.recipe.prepTimeMins || 15} min prep.`);

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
            <span className="text-[10px] text-slate-400 font-mono">
              USDA/ICMR-NIN estimate
            </span>
          </div>

          <h3 className="text-base font-serif text-[#421018] mt-1 font-semibold">
            {item.recipe.name}
          </h3>
          <p className="text-xs text-slate-600 font-light mt-0.5 max-w-2xl">
            {item.recipe.tagline}
          </p>

          {/* Scanned Pantry Ingredients Used */}
          {item.pantryStatus.matched && item.pantryStatus.matched.length > 0 && (
            <div className="mt-2 flex items-center gap-1.5 flex-wrap text-[11px] text-emerald-800 bg-emerald-50/80 border border-emerald-200/80 rounded-lg px-2.5 py-1 font-medium">
              <span className="font-bold">📦 Scanned In-Stock:</span>
              <span>{item.pantryStatus.matched.join(" · ")}</span>
            </div>
          )}

          {/* Plain-language explainability reason per Workflow Brief Section 1 & 6 */}
          <div className="mt-2 text-[11px] text-[#581825] bg-[#faf7f2] border border-[#ebdcd0] rounded-xl px-2.5 py-1.5 flex items-start gap-1.5 font-sans">
            <span className="shrink-0 text-xs">💡</span>
            <span className="leading-snug">{displayReason}</span>
          </div>

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
        <div className="flex items-center gap-1.5 flex-wrap sm:flex-col sm:items-end">
          <button
            onClick={() => onOpenRecipe(item.recipe)}
            className="px-3.5 py-2 rounded-xl bg-[#faf7f2] border border-[#d8c8b8] hover:bg-[#581825] hover:text-white text-[#581825] text-xs font-semibold transition-all shadow-sm flex items-center gap-1.5"
          >
            <span>📖</span> Recipe &amp; Prep
          </button>

          {item.availableAlternatives && item.availableAlternatives.length > 1 && onSelectAlternative && (
            <button
              onClick={() => setShowSwapModal(true)}
              className="px-3 py-1.5 rounded-xl bg-white border border-[#d8c8b8] hover:border-[#581825] text-slate-700 hover:text-[#581825] text-xs font-medium transition-all shadow-xs flex items-center gap-1"
              title="Choose another recipe that uses your scanned items"
            >
              <span>⇄</span> Swap ({item.availableAlternatives.length})
            </button>
          )}
        </div>

        <div className="flex items-center gap-1.5">
          {loggedStatus ? (
            <span className="px-3 py-1.5 rounded-xl bg-emerald-50 border border-emerald-200 text-emerald-800 text-xs font-semibold">
              {loggedStatus}
            </span>
          ) : (
            <>
              <button
                onClick={async () => {
                  setLoggedStatus("Eaten ✓");
                  try {
                    const { apiClient } = await import("@/lib/api-client");
                    await apiClient("/meal-logs", {
                      method: "POST",
                      body: JSON.stringify({
                        meal_id: item.recipe.id,
                        status: "eaten",
                      }),
                    });
                  } catch {
                    // local graceful fallback
                  }
                }}
                className="px-3 py-1.5 rounded-xl bg-white border border-emerald-300 hover:bg-emerald-50 text-emerald-700 text-xs font-semibold transition-all"
              >
                Mark Eaten ✓
              </button>
              <button
                onClick={async () => {
                  const allowed = ["time", "cost", "taste", "unavailable"];
                  const input = prompt("Skip reason? Choose: time, cost, taste, or unavailable") || "time";
                  const reason = input.toLowerCase().trim();
                  const validReason = allowed.includes(reason) ? reason : "time";
                  setLoggedStatus(`Skipped (${validReason})`);
                  try {
                    const { apiClient } = await import("@/lib/api-client");
                    await apiClient("/meal-logs", {
                      method: "POST",
                      body: JSON.stringify({
                        meal_id: item.recipe.id,
                        status: "skipped",
                        reason: validReason,
                        item_tags: [item.recipe.effortLevel === "low" ? "quick" : "long-prep-time"],
                      }),
                    });
                  } catch {
                    // local graceful fallback
                  }
                }}
                className="px-2.5 py-1.5 rounded-xl bg-white border border-slate-200 hover:bg-slate-50 text-slate-500 text-xs font-medium transition-all"
              >
                Skip ✕
              </button>
            </>
          )}
        </div>
      </div>

      {/* Alternative Dish Selection Modal */}
      {showSwapModal && item.availableAlternatives && onSelectAlternative && (
        <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/50 backdrop-blur-xs">
          <div className="bg-white rounded-3xl p-5 max-w-lg w-full max-h-[85vh] overflow-y-auto border border-[#e8ded3] shadow-2xl space-y-4">
            <div className="flex items-center justify-between border-b border-slate-100 pb-3">
              <div>
                <h4 className="text-base font-serif font-bold text-[#421018] flex items-center gap-2">
                  <span>⇄</span> Choose Recipe for {item.recipe.slotLabel}
                </h4>
                <p className="text-xs text-slate-500">
                  Select any recipe that matches your scanned groceries &amp; pantry stock.
                </p>
              </div>
              <button
                onClick={() => setShowSwapModal(false)}
                className="w-8 h-8 rounded-full bg-slate-100 text-slate-600 hover:bg-slate-200 flex items-center justify-center text-sm font-bold"
              >
                ✕
              </button>
            </div>

            <div className="space-y-2.5">
              {item.availableAlternatives.map((alt) => {
                const isSelected = alt.id === item.recipe.id;
                return (
                  <div
                    key={alt.id}
                    onClick={() => {
                      onSelectAlternative(item.key, alt.name);
                      setShowSwapModal(false);
                    }}
                    className={`p-3.5 rounded-2xl border cursor-pointer transition-all flex items-start justify-between gap-3 ${
                      isSelected
                        ? "border-[#581825] bg-[#fdf2f4]/60 ring-2 ring-[#581825]/20"
                        : "border-[#e8ded3] hover:border-[#581825]/50 bg-[#faf7f2]/50 hover:bg-[#faf7f2]"
                    }`}
                  >
                    <div className="flex items-start gap-3">
                      <span className="text-2xl p-2 rounded-xl bg-white border border-[#e2d6c9] shrink-0">
                        {alt.icon}
                      </span>
                      <div>
                        <div className="flex items-center gap-2 flex-wrap">
                          <span className="font-semibold text-sm text-[#421018]">{alt.name}</span>
                          <span className="text-[10px] bg-slate-100 text-slate-700 px-2 py-0.5 rounded-full font-medium">
                            {alt.effortLevel === "low" ? "⚡ <10m" : "🍳 ~20m"}
                          </span>
                        </div>
                        <p className="text-xs text-slate-600 font-light mt-0.5 line-clamp-1">
                          {alt.tagline}
                        </p>
                        <div className="mt-1.5 flex items-center gap-1.5 flex-wrap text-[10px] text-slate-500">
                          <span className="font-medium text-[#581825]">Ingredients:</span>
                          <span>{alt.requiredPantryItems.join(" · ")}</span>
                        </div>
                      </div>
                    </div>

                    <button
                      className={`px-3 py-1.5 rounded-xl text-xs font-semibold shrink-0 transition-all ${
                        isSelected
                          ? "bg-[#581825] text-white"
                          : "bg-white border border-[#d8c8b8] text-[#581825] hover:bg-[#581825] hover:text-white"
                      }`}
                    >
                      {isSelected ? "Active ✓" : "Select"}
                    </button>
                  </div>
                );
              })}
            </div>
          </div>
        </div>
      )}
    </div>
  );
};
