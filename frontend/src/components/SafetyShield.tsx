import React from "react";

export const SafetyShield: React.FC = () => {
  return (
    <div className="relative z-10 grid grid-cols-1 sm:grid-cols-2 gap-3">
      <div className="rounded-2xl bg-white p-4.5 border border-[#e8ded3] border-l-4 border-l-[#581825] shadow-sm">
        <h4 className="text-sm font-serif text-[#421018] flex items-center gap-2">
          <span>🚫</span> Active Safety Shield
        </h4>
        <div className="flex flex-wrap gap-1.5 mt-2.5">
          <span className="px-2.5 py-1 rounded-lg bg-[#fdf2f4] text-[#581825] border border-[#fbcfe8] text-xs font-medium">
            Tree Nuts (Blocked)
          </span>
          <span className="px-2.5 py-1 rounded-lg bg-[#eff6ff] text-[#1d4ed8] border border-[#bfdbfe] text-xs font-medium">
            Vegetarian
          </span>
          <span className="px-2.5 py-1 rounded-lg bg-[#faf7f2] text-slate-700 border border-[#e2d6c9] text-xs font-medium">
            1-Serving Portion Locked
          </span>
        </div>
      </div>
      <div className="rounded-2xl bg-white p-4.5 border border-[#e8ded3] border-l-4 border-l-[#1d4ed8] shadow-sm">
        <h4 className="text-sm font-serif text-[#421018] flex items-center gap-2">
          <span>🌿</span> WHO 2026 Dietary Compliance
        </h4>
        <ul className="text-xs text-slate-600 space-y-1.5 mt-2">
          <li>✓ Free Sugars: &lt; 4% total energy</li>
          <li>✓ Salt / Sodium: 3.8g / day (Target &lt; 5.0g)</li>
          <li>✓ Dietary Fibre: &gt; 32g / day across chosen meals</li>
        </ul>
      </div>
    </div>
  );
};
