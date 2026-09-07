import React from "react";
import { RecipeData } from "@/types";

interface RecipeModalProps {
  recipe: RecipeData | null;
  onClose: () => void;
}

export const RecipeModal: React.FC<RecipeModalProps> = ({ recipe, onClose }) => {
  if (!recipe) return null;

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-3 sm:p-6 bg-black/60 backdrop-blur-sm animate-fadeIn">
      <div className="relative w-full max-w-2xl max-h-[90vh] overflow-y-auto rounded-3xl bg-[#faf7f2] border border-[#d8c8b8] p-5 sm:p-7 shadow-2xl text-slate-800 space-y-5">
        {/* Modal Header */}
        <div className="flex items-start justify-between gap-4 border-b border-[#e9dfd5] pb-4">
          <div className="flex items-start gap-3">
            <div className="w-12 h-12 rounded-2xl bg-white border border-[#e2d6c9] flex items-center justify-center text-3xl shadow-sm">
              {recipe.icon}
            </div>
            <div>
              <div className="flex items-center gap-2 flex-wrap">
                <span className="text-xs uppercase font-bold text-[#581825]">
                  {recipe.slotLabel} · {recipe.timeSlot}
                </span>
                <span className="text-[10px] bg-[#eff6ff] text-[#1d4ed8] px-2 py-0.5 rounded-full border border-[#bfdbfe] font-semibold">
                  {recipe.effortLevel === "low" ? "⚡ Low Effort (<12m)" : "🍳 Moderate Effort (~25m)"}
                </span>
                <span className="text-[10px] bg-emerald-50 text-emerald-800 px-2 py-0.5 rounded-full border border-emerald-200 font-semibold">
                  👤 1 Solo Serving
                </span>
              </div>
              <h2 className="text-xl font-serif text-[#421018] font-bold mt-1">
                {recipe.name}
              </h2>
            </div>
          </div>

          <button
            onClick={onClose}
            className="w-8 h-8 rounded-full bg-white border border-[#d8c8b8] flex items-center justify-center text-slate-500 hover:text-black hover:bg-slate-100 transition-all font-bold shrink-0"
          >
            ✕
          </button>
        </div>

        {/* Timing & Summary Bar */}
        <div className="grid grid-cols-3 gap-2.5 text-center text-xs">
          <div className="p-2.5 rounded-xl bg-white border border-[#e2d6c9]">
            <p className="text-[10px] text-slate-500 uppercase font-semibold">Prep Time</p>
            <p className="text-sm font-bold text-[#421018] mt-0.5">{recipe.prepTimeMins} mins</p>
          </div>
          <div className="p-2.5 rounded-xl bg-white border border-[#e2d6c9]">
            <p className="text-[10px] text-slate-500 uppercase font-semibold">Cook Time</p>
            <p className="text-sm font-bold text-[#1d4ed8] mt-0.5">{recipe.cookTimeMins} mins</p>
          </div>
          <div className="p-2.5 rounded-xl bg-white border border-[#e2d6c9]">
            <p className="text-[10px] text-slate-500 uppercase font-semibold">Total Time</p>
            <p className="text-sm font-bold text-[#581825] mt-0.5">
              {recipe.prepTimeMins + recipe.cookTimeMins} mins
            </p>
          </div>
        </div>

        {/* Description */}
        <p className="text-xs text-slate-700 bg-white/80 p-3 rounded-xl border border-[#e8ded3] leading-relaxed">
          {recipe.description}
        </p>

        {/* Ingredients for 1 Person (Hinglish) */}
        <div>
          <h3 className="text-sm font-serif font-bold text-[#421018] flex items-center justify-between mb-2">
            <span>Exact Ingredients (1 Person Solo Portion)</span>
            <span className="text-[11px] font-sans text-slate-500 font-normal">
              ICMR-NIN &amp; USDA Verified
            </span>
          </h3>
          <div className="bg-white rounded-2xl border border-[#e8ded3] divide-y divide-slate-100 text-xs">
            {recipe.ingredients.map((ing, idx) => (
              <div key={idx} className="p-2.5 px-3.5 flex justify-between items-center">
                <span className="font-medium text-slate-800">
                  • {ing.name}{" "}
                  {ing.note ? (
                    <span className="text-slate-400 font-normal">({ing.note})</span>
                  ) : (
                    ""
                  )}
                </span>
                <span className="font-bold text-[#581825] shrink-0">{ing.quantity}</span>
              </div>
            ))}
          </div>
        </div>

        {/* Step-by-Step Solo Cooking Method (Hinglish) */}
        <div>
          <h3 className="text-sm font-serif font-bold text-[#421018] mb-2">
            Step-by-Step Cooking Instructions (Hinglish)
          </h3>
          <div className="space-y-2 text-xs">
            {recipe.steps.map((step, idx) => (
              <div
                key={idx}
                className="p-3 rounded-xl bg-white border border-[#e8ded3] flex gap-3 items-start"
              >
                <span className="w-5 h-5 rounded-full bg-[#eff6ff] text-[#1d4ed8] font-bold flex items-center justify-center shrink-0 border border-[#bfdbfe]">
                  {idx + 1}
                </span>
                <p className="text-slate-700 leading-relaxed">{step}</p>
              </div>
            ))}
          </div>
        </div>

        {/* Solo Living & Kitchen Hacks */}
        {recipe.soloHacks && recipe.soloHacks.length > 0 && (
          <div className="p-4 rounded-2xl bg-[#eff6ff] border border-[#bfdbfe] space-y-2">
            <h4 className="text-xs font-bold text-[#1d4ed8] flex items-center gap-1.5 uppercase tracking-wide">
              <span>💡</span> Solo Kitchen &amp; Dishwashing Hacks
            </h4>
            <ul className="text-xs text-slate-700 space-y-1">
              {recipe.soloHacks.map((hack, idx) => (
                <li key={idx} className="flex items-start gap-1.5">
                  <span className="text-[#1d4ed8]">✓</span>
                  <span>{hack}</span>
                </li>
              ))}
            </ul>
          </div>
        )}

        {/* Modal Footer */}
        <div className="pt-3 border-t border-[#e9dfd5] flex justify-end gap-2">
          <button
            onClick={onClose}
            className="px-4 py-2 rounded-xl bg-[#581825] hover:bg-[#722230] text-white text-xs font-semibold shadow-sm transition-all"
          >
            Sahi hai, bana raha hu! 🔥
          </button>
        </div>
      </div>
    </div>
  );
};
