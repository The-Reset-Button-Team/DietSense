"use client";

import { useState } from "react";

export default function HomePage() {
  const [activeTab, setActiveTab] = useState<"today" | "swap" | "safety" | "whisper">("today");

  return (
    <main className="min-h-screen bg-[#f5f0e8] text-slate-800 p-4 sm:p-8 flex items-center justify-center font-sans antialiased">
      {/* Atmos Container: Cream / Porcelain Base with Burgundy & Cobalt Blue Accents */}
      <div className="relative w-full max-w-4xl overflow-hidden rounded-3xl border border-[#e8ded3] bg-[#faf7f2] p-5 sm:p-8 shadow-xl text-slate-800">
        
        {/* Soft Ambient Glows */}
        <div className="absolute -top-24 -right-16 w-96 h-96 bg-[#dbeafe]/70 rounded-full blur-3xl pointer-events-none animate-pulse"></div>
        <div className="absolute -bottom-24 -left-16 w-96 h-96 bg-[#fce7f3]/50 rounded-full blur-3xl pointer-events-none animate-pulse"></div>

        {/* Top Atmospheric Header */}
        <div className="relative z-10 flex flex-col md:flex-row md:items-center justify-between gap-5 pb-6 border-b border-[#e9dfd5]">
          <div>
            <div className="inline-flex items-center gap-2 px-3 py-1 rounded-full bg-[#f3eae0] border border-[#d8c8b8] text-[#581825] text-xs font-medium tracking-wide mb-2.5 shadow-sm">
              <span className="w-2 h-2 rounded-full bg-[#581825] animate-pulse"></span>
              <span>DietSense Atmos · Gentle Nourishment</span>
            </div>
            <h1 className="text-2xl sm:text-3xl font-serif text-[#421018] tracking-tight">
              Good morning, <span className="text-[#1d4ed8] font-sans font-normal">Aarav</span>
            </h1>
            <p className="text-sm text-slate-600 mt-1 font-light max-w-xl">
              A steady, mindful day ahead. We have tailored meals to nurture your energy and support metabolic balance.
            </p>
          </div>

          {/* Daily Energy Harmony Gauge */}
          <div className="flex items-center gap-4 bg-white/90 border border-[#e2d6c9] rounded-2xl p-3.5 px-5 shadow-sm backdrop-blur-md">
            <div className="relative flex items-center justify-center">
              <svg className="w-13 h-13 transform -rotate-90" viewBox="0 0 48 48">
                <circle cx="24" cy="24" r="20" stroke="#f1e9df" strokeWidth="4.5" fill="transparent"/>
                <circle cx="24" cy="24" r="20" stroke="#1d4ed8" strokeWidth="4.5" strokeDasharray="125.6" strokeDashoffset="37.6" strokeLinecap="round" fill="transparent"/>
              </svg>
              <span className="absolute text-xs font-bold text-[#1d4ed8]">70%</span>
            </div>
            <div>
              <p className="text-[11px] uppercase tracking-wider text-slate-500 font-semibold">Daily Energy Harmony</p>
              <p className="text-base text-[#421018] font-serif font-semibold">1,420 <span className="text-xs font-sans text-slate-500 font-normal">/ 1,950 kcal</span></p>
            </div>
          </div>
        </div>

        {/* Macro Harmony Cards */}
        <div className="relative z-10 grid grid-cols-2 sm:grid-cols-4 gap-3 my-6">
          <div className="rounded-2xl bg-white/95 p-3.5 border border-[#e8ded3] shadow-sm">
            <div className="flex justify-between items-center text-xs text-slate-500 mb-1">
              <span className="font-medium text-slate-700">Carbohydrates</span>
              <span className="text-[11px] font-semibold text-[#1d4ed8] bg-[#eff6ff] px-1.5 py-0.5 rounded">55%</span>
            </div>
            <p className="text-lg font-semibold text-[#421018]">185g <span className="text-xs text-slate-400 font-normal">/ 240g</span></p>
            <div className="w-full bg-[#f1e9df] rounded-full h-1.5 mt-2.5 overflow-hidden">
              <div className="bg-gradient-to-r from-[#2563eb] to-[#60a5fa] h-full rounded-full" style={{ width: "77%" }}></div>
            </div>
          </div>

          <div className="rounded-2xl bg-white/95 p-3.5 border border-[#e8ded3] shadow-sm">
            <div className="flex justify-between items-center text-xs text-slate-500 mb-1">
              <span className="font-medium text-slate-700">Protein</span>
              <span className="text-[11px] font-semibold text-[#581825] bg-[#fdf2f4] px-1.5 py-0.5 rounded">Plant-rich</span>
            </div>
            <p className="text-lg font-semibold text-[#421018]">68g <span className="text-xs text-slate-400 font-normal">/ 85g</span></p>
            <div className="w-full bg-[#f1e9df] rounded-full h-1.5 mt-2.5 overflow-hidden">
              <div className="bg-gradient-to-r from-[#581825] to-[#801b2e] h-full rounded-full" style={{ width: "80%" }}></div>
            </div>
          </div>

          <div className="rounded-2xl bg-white/95 p-3.5 border border-[#e8ded3] shadow-sm">
            <div className="flex justify-between items-center text-xs text-slate-500 mb-1">
              <span className="font-medium text-slate-700">Healthy Fats</span>
              <span className="text-[11px] font-semibold text-[#0369a1] bg-[#f0f9ff] px-1.5 py-0.5 rounded">Unsaturated</span>
            </div>
            <p className="text-lg font-semibold text-[#421018]">42g <span className="text-xs text-slate-400 font-normal">/ 55g</span></p>
            <div className="w-full bg-[#f1e9df] rounded-full h-1.5 mt-2.5 overflow-hidden">
              <div className="bg-gradient-to-r from-[#0284c7] to-[#38bdf8] h-full rounded-full" style={{ width: "76%" }}></div>
            </div>
          </div>

          <div className="rounded-2xl bg-white/95 p-3.5 border border-[#e8ded3] shadow-sm">
            <div className="flex justify-between items-center text-xs text-slate-500 mb-1">
              <span className="font-medium text-slate-700">Dietary Fibre</span>
              <span className="text-[11px] font-semibold text-[#15803d] bg-[#f0fdf4] px-1.5 py-0.5 rounded">WHO Met ✓</span>
            </div>
            <p className="text-lg font-semibold text-[#15803d]">28g <span className="text-xs text-slate-400 font-normal">/ ≥25g</span></p>
            <div className="w-full bg-[#f1e9df] rounded-full h-1.5 mt-2.5 overflow-hidden">
              <div className="bg-[#15803d] h-full rounded-full" style={{ width: "100%" }}></div>
            </div>
          </div>
        </div>

        {/* Tab Buttons */}
        <div className="relative z-10 flex gap-2 pb-4 overflow-x-auto text-xs">
          <button
            onClick={() => setActiveTab("today")}
            className={`px-4 py-2 rounded-xl border transition-all font-medium ${
              activeTab === "today"
                ? "bg-[#581825] text-white border-[#581825] shadow-sm"
                : "border-[#d8c8b8] bg-white/80 text-slate-600 hover:text-[#581825]"
            }`}
          >
            🥣 Today's Nourishment
          </button>
          <button
            onClick={() => setActiveTab("swap")}
            className={`px-4 py-2 rounded-xl border transition-all font-medium ${
              activeTab === "swap"
                ? "bg-[#581825] text-white border-[#581825] shadow-sm"
                : "border-[#d8c8b8] bg-white/80 text-slate-600 hover:text-[#581825]"
            }`}
          >
            ✨ Mindful Swap
          </button>
          <button
            onClick={() => setActiveTab("safety")}
            className={`px-4 py-2 rounded-xl border transition-all font-medium ${
              activeTab === "safety"
                ? "bg-[#581825] text-white border-[#581825] shadow-sm"
                : "border-[#d8c8b8] bg-white/80 text-slate-600 hover:text-[#581825]"
            }`}
          >
            🛡️ Safety Shield
          </button>
          <button
            onClick={() => setActiveTab("whisper")}
            className={`px-4 py-2 rounded-xl border transition-all font-medium ${
              activeTab === "whisper"
                ? "bg-[#581825] text-white border-[#581825] shadow-sm"
                : "border-[#d8c8b8] bg-white/80 text-slate-600 hover:text-[#581825]"
            }`}
          >
            💬 DietSense Whisper
          </button>
        </div>

        {/* Tab 1: Today */}
        {activeTab === "today" && (
          <div className="relative z-10 space-y-3">
            <div className="rounded-2xl bg-white p-4.5 border border-[#e8ded3] flex flex-col sm:flex-row sm:items-center justify-between gap-4 border-l-4 border-l-[#1d4ed8] shadow-sm">
              <div className="flex items-start gap-3.5">
                <div className="w-12 h-12 rounded-2xl bg-[#eff6ff] border border-[#bfdbfe] flex items-center justify-center text-xl shrink-0">🥣</div>
                <div>
                  <div className="flex items-center gap-2">
                    <span className="text-[11px] uppercase tracking-wider text-[#1d4ed8] font-bold">Breakfast · 8:30 AM</span>
                    <span className="text-[10px] bg-[#f8fafc] text-slate-600 px-2 py-0.5 rounded-full border border-slate-200">ICMR-NIN Sourced</span>
                  </div>
                  <h3 className="text-base font-serif text-[#421018] mt-0.5">Spiced Oats & Moong Dal Porridge with Crushed Walnuts</h3>
                  <p className="text-xs text-slate-600 font-light mt-0.5">Rich unrefined complex carbohydrates and prebiotic fibre for lasting morning energy.</p>
                </div>
              </div>
              <div className="flex items-center justify-between sm:justify-end gap-4 shrink-0 pt-2 sm:pt-0 border-t sm:border-t-0 border-slate-100">
                <div className="text-right">
                  <p className="text-sm font-semibold text-[#421018]">380 <span className="text-xs font-normal text-slate-400">kcal</span></p>
                  <p className="text-[11px] text-[#1d4ed8] font-medium">14g protein · 8g fibre</p>
                </div>
                <button className="px-3 py-1.5 rounded-xl bg-[#581825] hover:bg-[#722230] text-white text-xs font-medium transition-all shadow-sm">Enjoyed ✓</button>
              </div>
            </div>

            <div className="rounded-2xl bg-white p-4.5 border border-[#e8ded3] flex flex-col sm:flex-row sm:items-center justify-between gap-4 border-l-4 border-l-[#581825] shadow-sm">
              <div className="flex items-start gap-3.5">
                <div className="w-12 h-12 rounded-2xl bg-[#fdf2f4] border border-[#fbcfe8] flex items-center justify-center text-xl shrink-0">🥗</div>
                <div>
                  <div className="flex items-center gap-2">
                    <span className="text-[11px] uppercase tracking-wider text-[#581825] font-bold">Lunch · 1:15 PM</span>
                    <span className="text-[10px] bg-[#eff6ff] text-[#1d4ed8] px-2 py-0.5 rounded-full border border-[#bfdbfe] font-medium">SHAP Score: 0.94</span>
                  </div>
                  <h3 className="text-base font-serif text-[#421018] mt-0.5">Brown Rice Bowl with Palak Dal & Sautéed Paneer</h3>
                  <p className="text-xs text-slate-600 font-light mt-0.5">High bioavailable iron and plant calcium. Seasoned lightly with cold-pressed mustard oil.</p>
                </div>
              </div>
              <div className="flex items-center justify-between sm:justify-end gap-4 shrink-0 pt-2 sm:pt-0 border-t sm:border-t-0 border-slate-100">
                <div className="text-right">
                  <p className="text-sm font-semibold text-[#421018]">560 <span className="text-xs font-normal text-slate-400">kcal</span></p>
                  <p className="text-[11px] text-[#1d4ed8] font-medium">26g protein · 11g fibre</p>
                </div>
                <button className="px-3 py-1.5 rounded-xl bg-[#581825] hover:bg-[#722230] text-white text-xs font-medium transition-all shadow-sm">Enjoyed ✓</button>
              </div>
            </div>

            <div className="rounded-2xl bg-white p-4.5 border border-[#e8ded3] flex flex-col sm:flex-row sm:items-center justify-between gap-4 border-l-4 border-l-[#0284c7] shadow-sm">
              <div className="flex items-start gap-3.5">
                <div className="w-12 h-12 rounded-2xl bg-[#f0f9ff] border border-[#bae6fd] flex items-center justify-center text-xl shrink-0">🍵</div>
                <div>
                  <div className="flex items-center gap-2">
                    <span className="text-[11px] uppercase tracking-wider text-[#0284c7] font-bold">Evening Pause · 5:00 PM</span>
                  </div>
                  <h3 className="text-base font-serif text-[#421018] mt-0.5">Roasted Makhana with Green Cardamom Infusion</h3>
                  <p className="text-xs text-slate-600 font-light mt-0.5">Zero added free sugars. Rich in magnesium for evening restorative relaxation.</p>
                </div>
              </div>
              <div className="flex items-center justify-between sm:justify-end gap-4 shrink-0 pt-2 sm:pt-0 border-t sm:border-t-0 border-slate-100">
                <div className="text-right">
                  <p className="text-sm font-semibold text-[#421018]">140 <span className="text-xs font-normal text-slate-400">kcal</span></p>
                  <p className="text-[11px] text-[#0284c7] font-medium">4g protein · 3g fibre</p>
                </div>
                <button className="px-3 py-1.5 rounded-xl border border-[#d8c8b8] bg-[#fdfbf7] hover:bg-[#f3eae0] text-[#581825] text-xs font-medium transition-all">Mark Eaten</button>
              </div>
            </div>
          </div>
        )}

        {/* Tab 2: Swap */}
        {activeTab === "swap" && (
          <div className="relative z-10 space-y-4">
            <div className="rounded-2xl bg-white p-5 border border-[#e8ded3] shadow-sm">
              <div className="flex items-center gap-3 mb-3">
                <span className="text-2xl">🔄</span>
                <div>
                  <h3 className="text-base font-serif text-[#421018]">Desire something different for dinner?</h3>
                  <p className="text-xs text-slate-500 font-light">DietSense recalculated validated alternatives while preserving your daily targets:</p>
                </div>
              </div>
              <div className="grid grid-cols-1 md:grid-cols-2 gap-3 mt-4">
                <div className="p-4 rounded-xl bg-[#faf7f2] border border-[#e2d6c9] relative">
                  <span className="absolute top-3 right-3 text-[10px] bg-[#eff6ff] text-[#1d4ed8] border border-[#bfdbfe] px-2 py-0.5 rounded-full font-bold">96% Macro Match</span>
                  <h4 className="text-sm font-semibold text-[#421018]">Grilled Tofu Veggie Wrap</h4>
                  <p className="text-xs text-slate-600 mt-1 font-light">Whole wheat roti base, steamed capsicum, mint yogurt drizzle.</p>
                  <div className="flex items-center justify-between mt-3 text-xs">
                    <span className="text-slate-700 font-medium">355 kcal · 18g Protein</span>
                    <button className="px-3 py-1 rounded-lg bg-[#581825] hover:bg-[#722230] text-white font-medium text-[11px] transition-all">Select This</button>
                  </div>
                </div>

                <div className="p-4 rounded-xl bg-[#faf7f2] border border-[#e2d6c9] relative">
                  <span className="absolute top-3 right-3 text-[10px] bg-[#f0f9ff] text-[#0284c7] border border-[#bae6fd] px-2 py-0.5 rounded-full font-bold">91% Macro Match</span>
                  <h4 className="text-sm font-semibold text-[#421018]">Lentil Quinoa Broth Bowl</h4>
                  <p className="text-xs text-slate-600 mt-1 font-light">Warm cumin broth, roasted cumin seeds, crushed flaxseed topping.</p>
                  <div className="flex items-center justify-between mt-3 text-xs">
                    <span className="text-slate-700 font-medium">330 kcal · 15g Protein</span>
                    <button className="px-3 py-1 rounded-lg bg-white border border-[#d8c8b8] hover:bg-[#f3eae0] text-[#581825] font-medium text-[11px] transition-all">Select This</button>
                  </div>
                </div>
              </div>
            </div>
          </div>
        )}

        {/* Tab 3: Safety */}
        {activeTab === "safety" && (
          <div className="relative z-10 grid grid-cols-1 sm:grid-cols-2 gap-3">
            <div className="rounded-2xl bg-white p-4.5 border border-[#e8ded3] border-l-4 border-l-[#581825] shadow-sm">
              <h4 className="text-sm font-serif text-[#421018] flex items-center gap-2">
                <span>🚫</span> Active Safety Shield
              </h4>
              <div className="flex flex-wrap gap-1.5 mt-2.5">
                <span className="px-2.5 py-1 rounded-lg bg-[#fdf2f4] text-[#581825] border border-[#fbcfe8] text-xs font-medium">Tree Nuts / Peanuts (Blocked)</span>
                <span className="px-2.5 py-1 rounded-lg bg-[#eff6ff] text-[#1d4ed8] border border-[#bfdbfe] text-xs font-medium">Vegetarian</span>
              </div>
              <p className="text-[11px] text-slate-500 mt-2 font-light">Rule 2 in action: Hard constraint filter blocked 142 recipes with nut traces before recommendation scoring.</p>
            </div>

            <div className="rounded-2xl bg-white p-4.5 border border-[#e8ded3] border-l-4 border-l-[#1d4ed8] shadow-sm">
              <h4 className="text-sm font-serif text-[#421018] flex items-center gap-2">
                <span>🌿</span> WHO 2026 Dietary Guidelines
              </h4>
              <ul className="text-xs text-slate-600 space-y-1.5 mt-2 font-light">
                <li className="flex items-center gap-2"><span className="text-[#15803d] font-bold">✓</span> Free Sugars: &lt; 4% total energy (WHO target &lt; 5%)</li>
                <li className="flex items-center gap-2"><span className="text-[#15803d] font-bold">✓</span> Salt & Sodium: 3.8g salt / day (WHO target &lt; 5.0g)</li>
                <li className="flex items-center gap-2"><span className="text-[#15803d] font-bold">✓</span> Fresh Vegetables & Fruit: 480g / day (Target ≥ 400g)</li>
              </ul>
            </div>
          </div>
        )}

        {/* Tab 4: Whisper */}
        {activeTab === "whisper" && (
          <div className="relative z-10 p-4.5 rounded-2xl bg-white border border-[#e8ded3] shadow-sm space-y-3">
            <div className="flex items-start gap-3">
              <div className="w-8 h-8 rounded-full bg-[#fdf2f4] border border-[#fbcfe8] flex items-center justify-center text-sm shrink-0">🌿</div>
              <div className="bg-[#faf7f2] border border-[#e2d6c9] rounded-2xl rounded-tl-none p-3.5 text-xs text-slate-700 font-light max-w-lg leading-relaxed">
                I noticed you had a slightly busier morning. How did your energy feel after the moong dal porridge? We can adjust the lunch portions if you would prefer something lighter.
              </div>
            </div>
          </div>
        )}

        {/* Footer */}
        <div className="relative z-10 mt-6 pt-4 border-t border-[#e9dfd5] flex flex-col sm:flex-row items-center justify-between text-[11px] text-slate-500 font-light gap-2">
          <span>DietSense Atmos · White, Cream, Blue &amp; Burgundy Palette</span>
          <span className="text-[#581825] font-serif font-medium">Every calorie is calculated, never hallucinated.</span>
        </div>

      </div>
    </main>
  );
}
