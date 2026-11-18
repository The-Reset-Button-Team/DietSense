"use client";

import React, { useState, useEffect } from "react";
import { aiApi } from "@/lib/ai-client";
import { ExplainRecommendationResponse } from "@/types/ai";

interface AIExplanationModalProps {
  foodId: number | null;
  foodName: string;
  isOpen: boolean;
  onClose: () => void;
  onAskAboutMeal?: (foodId: number, foodName: string) => void;
}

export const AIExplanationModal: React.FC<AIExplanationModalProps> = ({
  foodId,
  foodName,
  isOpen,
  onClose,
  onAskAboutMeal,
}) => {
  const [loading, setLoading] = useState<boolean>(true);
  const [data, setData] = useState<ExplainRecommendationResponse | null>(null);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (!isOpen || foodId === null) return;

    let isMounted = true;
    setLoading(true);
    setError(null);

    aiApi
      .explainRecommendation(foodId, { tone: "friendly", food_name: foodName })
      .then((res) => {
        if (isMounted) {
          setData(res);
          setLoading(false);
        }
      })
      .catch((err) => {
        if (isMounted) {
          setError(err?.message || "Failed to fetch AI explanation. Please try again.");
          setLoading(false);
        }
      });

    return () => {
      isMounted = false;
    };
  }, [isOpen, foodId, foodName]);

  if (!isOpen) return null;

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-3 sm:p-6 bg-black/60 backdrop-blur-sm animate-fadeIn">
      <div className="relative w-full max-w-xl max-h-[90vh] overflow-y-auto rounded-3xl bg-[#faf7f2] border border-[#d8c8b8] p-5 sm:p-7 shadow-2xl text-slate-800 space-y-5">
        {/* Header */}
        <div className="flex items-start justify-between gap-4 border-b border-[#e9dfd5] pb-4">
          <div>
            <div className="flex items-center gap-2">
              <span className="text-xs uppercase font-bold text-[#581825] tracking-wider flex items-center gap-1.5">
                <span>✨</span> AI Recommendation Breakdown
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

        {/* Loading State */}
        {loading && (
          <div className="py-12 flex flex-col items-center justify-center gap-3">
            <div className="w-8 h-8 border-3 border-[#581825] border-t-transparent rounded-full animate-spin" />
            <p className="text-xs text-slate-500 font-medium animate-pulse">
              Consulting USDA &amp; ICMR-NIN verified nutrition data...
            </p>
          </div>
        )}

        {/* Error State */}
        {!loading && error && (
          <div className="p-4 rounded-2xl bg-red-50 border border-red-200 text-red-800 text-xs space-y-2">
            <p className="font-semibold flex items-center gap-1.5">
              <span>⚠️</span> Unable to load explanation
            </p>
            <p className="text-red-700">{error}</p>
            <button
              onClick={() => {
                if (foodId !== null) {
                  setLoading(true);
                  setError(null);
                  aiApi
                    .explainRecommendation(foodId, { tone: "friendly", food_name: foodName })
                    .then((res) => {
                      setData(res);
                      setLoading(false);
                    })
                    .catch((err) => {
                      setError(err?.message || "Failed to load");
                      setLoading(false);
                    });
                }
              }}
              className="mt-2 px-3 py-1.5 bg-red-800 text-white rounded-lg font-semibold hover:bg-red-900 transition-all"
            >
              Retry
            </button>
          </div>
        )}

        {/* Success State */}
        {!loading && data && (
          <div className="space-y-4">
            {/* Headline Card */}
            <div className="p-3.5 rounded-2xl bg-white border border-[#e8ded3] shadow-xs">
              <p className="text-xs font-semibold text-[#581825]">
                {data.headline}
              </p>
              <p className="text-xs text-slate-700 mt-1 leading-relaxed">
                {data.explanation}
              </p>
            </div>

            {/* Key Benefits */}
            {data.key_benefits && data.key_benefits.length > 0 && (
              <div className="p-3.5 rounded-2xl bg-[#eff6ff] border border-[#bfdbfe] space-y-1.5">
                <h4 className="text-xs font-bold text-[#1d4ed8] uppercase tracking-wide flex items-center gap-1">
                  <span>💪</span> Key Health Benefits
                </h4>
                <ul className="text-xs text-slate-700 space-y-1">
                  {data.key_benefits.map((b, idx) => (
                    <li key={idx} className="flex items-start gap-1.5">
                      <span className="text-emerald-600 font-bold">✓</span>
                      <span>{b}</span>
                    </li>
                  ))}
                </ul>
              </div>
            )}

            {/* Preparation Tip */}
            {data.preparation_tip && (
              <div className="p-3 rounded-2xl bg-amber-50/80 border border-amber-200 text-amber-900 text-xs flex items-start gap-2">
                <span className="text-base shrink-0">🍳</span>
                <div>
                  <span className="font-bold">Chef Tip:</span> {data.preparation_tip}
                </div>
              </div>
            )}

            {/* Verified Nutrition Grid */}
            <div className="p-3.5 rounded-2xl bg-white border border-[#e8ded3] space-y-2">
              <div className="flex items-center justify-between">
                <span className="text-[11px] font-bold text-[#421018] uppercase tracking-wider">
                  Verified Nutrition Context (Per Serving)
                </span>
                <span className="text-[10px] text-slate-400 font-mono">
                  USDA / ICMR-NIN Ground Truth
                </span>
              </div>
              <div className="grid grid-cols-4 gap-2 text-center text-xs">
                <div className="p-2 rounded-xl bg-[#faf7f2] border border-[#e2d6c9]">
                  <p className="text-[10px] text-slate-500">Calories</p>
                  <p className="text-sm font-bold text-[#421018]">
                    {data.verified_nutrition.calories_kcal} kcal
                  </p>
                </div>
                <div className="p-2 rounded-xl bg-[#faf7f2] border border-[#e2d6c9]">
                  <p className="text-[10px] text-slate-500">Protein</p>
                  <p className="text-sm font-bold text-[#581825]">
                    {data.verified_nutrition.protein_g}g
                  </p>
                </div>
                <div className="p-2 rounded-xl bg-[#faf7f2] border border-[#e2d6c9]">
                  <p className="text-[10px] text-slate-500">Carbs</p>
                  <p className="text-sm font-bold text-[#1d4ed8]">
                    {data.verified_nutrition.carbohydrates_g}g
                  </p>
                </div>
                <div className="p-2 rounded-xl bg-[#faf7f2] border border-[#e2d6c9]">
                  <p className="text-[10px] text-slate-500">Fat</p>
                  <p className="text-sm font-bold text-[#0369a1]">
                    {data.verified_nutrition.fat_g}g
                  </p>
                </div>
              </div>
            </div>

            {/* Medical Disclaimer */}
            <p className="text-[10px] text-slate-400 italic text-center">
              {data.disclaimer}
            </p>
          </div>
        )}

        {/* Footer Actions */}
        <div className="pt-3 border-t border-[#e9dfd5] flex items-center justify-between gap-2">
          {onAskAboutMeal && foodId !== null ? (
            <button
              onClick={() => {
                onClose();
                onAskAboutMeal(foodId, foodName);
              }}
              className="px-3.5 py-2 rounded-xl bg-white border border-[#d8c8b8] text-[#581825] hover:bg-[#faf7f2] text-xs font-semibold flex items-center gap-1.5 transition-all shadow-xs"
            >
              <span>💬</span> Ask AI about this meal
            </button>
          ) : <div />}

          <button
            onClick={onClose}
            className="px-4 py-2 rounded-xl bg-[#581825] hover:bg-[#722230] text-white text-xs font-semibold shadow-sm transition-all"
          >
            Got it ✓
          </button>
        </div>
      </div>
    </div>
  );
};
