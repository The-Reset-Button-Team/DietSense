"use client";

import React, { useState, useEffect, useCallback } from "react";
import { aiApi } from "@/lib/ai-client";
import { CookingInstructionResponse } from "@/types/ai";

interface CookingInstructionsModalProps {
  foodId: number | null;
  foodName: string;
  isOpen: boolean;
  onClose: () => void;
}

export const CookingInstructionsModal: React.FC<CookingInstructionsModalProps> = ({
  foodId,
  foodName,
  isOpen,
  onClose,
}) => {
  const [servings, setServings] = useState<number>(1);
  const [skillLevel, setSkillLevel] = useState<string>("beginner");
  const [loading, setLoading] = useState<boolean>(true);
  const [data, setData] = useState<CookingInstructionResponse | null>(null);
  const [error, setError] = useState<string | null>(null);

  const fetchInstructions = useCallback(() => {
    if (!isOpen || foodId === null) return;
    setLoading(true);
    setError(null);

    aiApi
      .getCookingInstructions(foodId, { servings, skill_level: skillLevel, food_name: foodName })
      .then((res) => {
        setData(res);
        setLoading(false);
      })
      .catch((err) => {
        setError(err?.message || "Failed to generate cooking instructions.");
        setLoading(false);
      });
  }, [isOpen, foodId, servings, skillLevel, foodName]);

  useEffect(() => {
    fetchInstructions();
  }, [fetchInstructions]);

  if (!isOpen) return null;

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-3 sm:p-6 bg-black/60 backdrop-blur-sm animate-fadeIn">
      <div className="relative w-full max-w-2xl max-h-[90vh] overflow-y-auto rounded-3xl bg-[#faf7f2] border border-[#d8c8b8] p-5 sm:p-7 shadow-2xl text-slate-800 space-y-5">
        {/* Header */}
        <div className="flex items-start justify-between gap-4 border-b border-[#e9dfd5] pb-4">
          <div>
            <div className="flex items-center gap-2">
              <span className="text-xs uppercase font-bold text-[#581825] tracking-wider flex items-center gap-1.5">
                <span>👨‍🍳</span> AI Cooking Assistant
              </span>
              {data && (
                <span className="text-[10px] bg-[#eff6ff] text-[#1d4ed8] px-2 py-0.5 rounded-full border border-[#bfdbfe] font-mono">
                  {data.source === "offline_fallback" ? "Evidence Engine" : "Gemini 3.8 Flash"}
                </span>
              )}
            </div>
            <h2 className="text-xl font-serif text-[#421018] font-bold mt-1">
              {foodName}
            </h2>
          </div>

          <button
            onClick={onClose}
            className="w-8 h-8 rounded-full bg-white border border-[#d8c8b8] flex items-center justify-center text-slate-500 hover:text-black hover:bg-slate-100 transition-all font-bold shrink-0"
            aria-label="Close modal"
          >
            ✕
          </button>
        </div>

        {/* Controls: Servings & Skill Level */}
        <div className="flex flex-wrap items-center justify-between gap-3 p-3 bg-white rounded-2xl border border-[#e8ded3] text-xs">
          <div className="flex items-center gap-2">
            <span className="font-semibold text-slate-600">Servings:</span>
            <div className="flex items-center gap-1">
              {[1, 2, 4].map((num) => (
                <button
                  key={num}
                  onClick={() => setServings(num)}
                  className={`px-2.5 py-1 rounded-lg border font-medium transition-all ${
                    servings === num
                      ? "bg-[#581825] text-white border-[#581825]"
                      : "bg-[#faf7f2] border-[#d8c8b8] text-slate-600 hover:text-[#581825]"
                  }`}
                >
                  {num} {num === 1 ? "Person" : "People"}
                </button>
              ))}
            </div>
          </div>

          <div className="flex items-center gap-2">
            <span className="font-semibold text-slate-600">Skill Level:</span>
            <div className="flex items-center gap-1">
              {["beginner", "intermediate"].map((level) => (
                <button
                  key={level}
                  onClick={() => setSkillLevel(level)}
                  className={`px-2.5 py-1 rounded-lg border capitalize font-medium transition-all ${
                    skillLevel === level
                      ? "bg-[#581825] text-white border-[#581825]"
                      : "bg-[#faf7f2] border-[#d8c8b8] text-slate-600 hover:text-[#581825]"
                  }`}
                >
                  {level}
                </button>
              ))}
            </div>
          </div>
        </div>

        {/* Loading State */}
        {loading && (
          <div className="py-12 flex flex-col items-center justify-center gap-3">
            <div className="w-8 h-8 border-3 border-[#581825] border-t-transparent rounded-full animate-spin" />
            <p className="text-xs text-slate-500 font-medium animate-pulse">
              Generating tailored cooking instructions...
            </p>
          </div>
        )}

        {/* Error State */}
        {!loading && error && (
          <div className="p-4 rounded-2xl bg-red-50 border border-red-200 text-red-800 text-xs space-y-2">
            <p className="font-semibold flex items-center gap-1.5">
              <span>⚠️</span> Unable to generate instructions
            </p>
            <p className="text-red-700">{error}</p>
            <button
              onClick={fetchInstructions}
              className="mt-2 px-3 py-1.5 bg-red-800 text-white rounded-lg font-semibold hover:bg-red-900 transition-all"
            >
              Retry
            </button>
          </div>
        )}

        {/* Success State */}
        {!loading && data && (
          <div className="space-y-4">
            {/* Timing & Equipment Bar */}
            <div className="grid grid-cols-2 sm:grid-cols-4 gap-2 text-center text-xs">
              <div className="p-2.5 rounded-xl bg-white border border-[#e2d6c9]">
                <p className="text-[10px] text-slate-500 uppercase font-semibold">Prep Time</p>
                <p className="text-sm font-bold text-[#421018] mt-0.5">{data.prep_time_mins} mins</p>
              </div>
              <div className="p-2.5 rounded-xl bg-white border border-[#e2d6c9]">
                <p className="text-[10px] text-slate-500 uppercase font-semibold">Cook Time</p>
                <p className="text-sm font-bold text-[#1d4ed8] mt-0.5">{data.cook_time_mins} mins</p>
              </div>
              <div className="p-2.5 rounded-xl bg-white border border-[#e2d6c9]">
                <p className="text-[10px] text-slate-500 uppercase font-semibold">Servings</p>
                <p className="text-sm font-bold text-[#581825] mt-0.5">{data.servings}</p>
              </div>
              <div className="p-2.5 rounded-xl bg-white border border-[#e2d6c9]">
                <p className="text-[10px] text-slate-500 uppercase font-semibold">Calories</p>
                <p className="text-sm font-bold text-emerald-700 mt-0.5">
                  {data.verified_nutrition.calories_kcal} kcal
                </p>
              </div>
            </div>

            {/* Equipment Needed */}
            {data.equipment_needed && data.equipment_needed.length > 0 && (
              <div className="p-3 bg-white rounded-2xl border border-[#e8ded3] text-xs">
                <span className="font-bold text-[#421018] flex items-center gap-1.5 mb-1.5">
                  <span>🍳</span> Equipment Needed:
                </span>
                <div className="flex flex-wrap gap-1.5">
                  {data.equipment_needed.map((eq, idx) => (
                    <span
                      key={idx}
                      className="px-2 py-0.5 bg-[#faf7f2] border border-[#d8c8b8] text-slate-700 rounded-lg text-[11px]"
                    >
                      {eq}
                    </span>
                  ))}
                </div>
              </div>
            )}

            {/* Ingredients */}
            {data.ingredients && data.ingredients.length > 0 && (
              <div className="space-y-1.5">
                <h4 className="text-xs font-bold text-[#421018] uppercase tracking-wide flex items-center justify-between">
                  <span>Exact Ingredients ({data.servings} Serving{data.servings > 1 ? "s" : ""})</span>
                  <span className="text-[10px] text-slate-400 font-normal">USDA Ground Truth</span>
                </h4>
                <div className="bg-white rounded-2xl border border-[#e8ded3] divide-y divide-slate-100 text-xs">
                  {data.ingredients.map((ing, idx) => (
                    <div key={idx} className="p-2.5 px-3.5 flex items-center justify-between">
                      <span className="font-medium text-slate-700">• {ing}</span>
                    </div>
                  ))}
                </div>
              </div>
            )}

            {/* Step-by-Step Instructions */}
            <div className="space-y-2">
              <h4 className="text-xs font-bold text-[#421018] uppercase tracking-wide">
                Step-by-Step Instructions
              </h4>
              <div className="space-y-2 text-xs">
                {data.step_by_step_instructions.map((step, idx) => (
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

            {/* Chef Tips */}
            {data.chef_tips && data.chef_tips.length > 0 && (
              <div className="p-3.5 rounded-2xl bg-amber-50/80 border border-amber-200 space-y-1.5">
                <h4 className="text-xs font-bold text-amber-900 uppercase tracking-wide flex items-center gap-1.5">
                  <span>💡</span> Healthy Chef Tips
                </h4>
                <ul className="text-xs text-amber-800 space-y-1">
                  {data.chef_tips.map((tip, idx) => (
                    <li key={idx} className="flex items-start gap-1.5">
                      <span>✓</span>
                      <span>{tip}</span>
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
            Done Cooking ✓
          </button>
        </div>
      </div>
    </div>
  );
};
