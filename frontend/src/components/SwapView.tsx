import React from "react";

interface SwapViewProps {
  targetCalories: number;
}

export const SwapView: React.FC<SwapViewProps> = ({ targetCalories }) => {
  return (
    <div className="relative z-10 space-y-4">
      <div className="rounded-2xl bg-white p-5 border border-[#e8ded3] shadow-sm">
        <h3 className="text-base font-serif text-[#421018]">Mindful Swap Generator</h3>
        <p className="text-xs text-slate-500 font-light mt-1">
          Calculated alternatives maintaining your {targetCalories} kcal target:
        </p>
        <div className="grid grid-cols-1 md:grid-cols-2 gap-3 mt-4">
          <div className="p-4 rounded-xl bg-[#faf7f2] border border-[#e2d6c9]">
            <span className="text-[10px] bg-[#eff6ff] text-[#1d4ed8] border border-[#bfdbfe] px-2 py-0.5 rounded-full font-bold">
              96% Macro Match
            </span>
            <h4 className="text-sm font-semibold text-[#421018] mt-2">Grilled Tofu Veggie Wrap</h4>
            <p className="text-xs text-slate-600 mt-1">355 kcal · 18g Protein · 8m Low Effort</p>
          </div>
          <div className="p-4 rounded-xl bg-[#faf7f2] border border-[#e2d6c9]">
            <span className="text-[10px] bg-[#f0f9ff] text-[#0284c7] border border-[#bae6fd] px-2 py-0.5 rounded-full font-bold">
              91% Macro Match
            </span>
            <h4 className="text-sm font-semibold text-[#421018] mt-2">Lentil Quinoa Broth Bowl</h4>
            <p className="text-xs text-slate-600 mt-1">330 kcal · 15g Protein · 1-Pot Express</p>
          </div>
        </div>
      </div>
    </div>
  );
};
