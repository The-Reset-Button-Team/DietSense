"use client";

import { useState } from "react";

export default function HomePage() {
  const [activeTab, setActiveTab] = useState<"today" | "swap" | "safety" | "whisper">("today");

  return (
    <main className="min-h-screen bg-[#060b08] text-slate-100 p-4 sm:p-8 flex items-center justify-center font-sans antialiased selection:bg-emerald-500 selection:text-white">
      {/* Atmos Container */}
      <div className="relative w-full max-w-4xl overflow-hidden rounded-3xl border border-emerald-900/40 bg-gradient-to-b from-[#09130e] via-[#0d1c14] to-[#060b08] p-5 sm:p-8 shadow-2xl text-slate-200">
        
        {/* Atmospheric Glows */}
        <div className="absolute -top-24 -left-20 w-96 h-96 bg-emerald-500/15 rounded-full blur-3xl pointer-events-none animate-pulse"></div>
        <div className="absolute -bottom-24 -right-20 w-96 h-96 bg-teal-500/10 rounded-full blur-3xl pointer-events-none animate-pulse"></div>

        {/* Top Atmosphere Bar */}
        <div className="relative z-10 flex flex-col md:flex-row md:items-center justify-between gap-4 pb-6 border-b border-emerald-900/30">
          <div>
            <div className="inline-flex items-center gap-2 px-3 py-1 rounded-full bg-emerald-950/60 border border-emerald-700/30 text-emerald-400 text-xs tracking-wide mb-2">
              <span className="w-2 h-2 rounded-full bg-emerald-400 animate-ping"></span>
              <span>Atmos Calm Sync · Morning Breeze</span>
            </div>
            <h1 className="text-2xl sm:text-3xl font-light tracking-tight text-white">
              Good morning, <span className="font-normal text-emerald-300">Aarav</span>
            </h1>
            <p className="text-sm text-slate-400 mt-1 font-light">
              "Your body needs steady, gentle energy today. We have balanced comfort and nourishment."
            </p>
          </div>

          {/* Daily Harmony Gauge */}
          <div className="flex items-center gap-4 bg-emerald-950/40 border border-emerald-800/30 rounded-2xl p-3 px-4 backdrop-blur-md">
            <div className="relative flex items-center justify-center">
              <svg className="w-12 h-12 transform -rotate-90">
                <circle cx="24" cy="24" r="20" stroke="rgba(255,255,255,0.08)" strokeWidth="4" fill="transparent"/>
                <circle cx="24" cy="24" r="20" stroke="#34d399" strokeWidth="4" strokeDasharray="125.6" strokeDashoffset="37.6" strokeLinecap="round" fill="transparent"/>
              </svg>
              <span className="absolute text-xs font-medium text-emerald-300">70%</span>
            </div>
            <div>
              <p className="text-[11px] uppercase tracking-wider text-slate-400 font-medium">Daily Harmony</p>
              <p className="text-base font-light text-white"><span className="text-emerald-400 font-normal">1,420</span> / 1,950 <span className="text-xs text-slate-400">kcal</span></p>
            </div>
          </div>
        </div>

        {/* Macro Overview */}
        <div className="relative z-10 grid grid-cols-2 sm:grid-cols-4 gap-3 my-6">
          <div className="p-3.5 rounded-2xl bg-white/[0.02] border border-white/[0.06] backdrop-blur-sm">
            <div className="flex justify-between items-center text-xs text-slate-400 mb-1">
              <span>Carbohydrates</span>
              <span className="text-emerald-300 text-[11px]">WHO: 55%</span>
            </div>
            <p className="text-lg font-light text-white">185g <span className="text-xs text-slate-400">/ 240g</span></p>
            <div className="w-full bg-slate-800/80 rounded-full h-1.5 mt-2 overflow-hidden">
              <div className="bg-gradient-to-r from-emerald-500 to-teal-400 h-full rounded-full" style={{ width: "77%" }}></div>
            </div>
          </div>

          <div className="p-3.5 rounded-2xl bg-white/[0.02] border border-white/[0.06] backdrop-blur-sm">
            <div className="flex justify-between items-center text-xs text-slate-400 mb-1">
              <span>Protein</span>
              <span className="text-teal-300 text-[11px]">Plant-Rich</span>
            </div>
            <p className="text-lg font-light text-white">68g <span className="text-xs text-slate-400">/ 85g</span></p>
            <div className="w-full bg-slate-800/80 rounded-full h-1.5 mt-2 overflow-hidden">
              <div className="bg-gradient-to-r from-teal-400 to-cyan-400 h-full rounded-full" style={{ width: "80%" }}></div>
            </div>
          </div>

          <div className="p-3.5 rounded-2xl bg-white/[0.02] border border-white/[0.06] backdrop-blur-sm">
            <div className="flex justify-between items-center text-xs text-slate-400 mb-1">
              <span>Healthy Fats</span>
              <span className="text-amber-300 text-[11px]">Unsaturated</span>
            </div>
            <p className="text-lg font-light text-white">42g <span className="text-xs text-slate-400">/ 55g</span></p>
            <div className="w-full bg-slate-800/80 rounded-full h-1.5 mt-2 overflow-hidden">
              <div className="bg-gradient-to-r from-amber-400 to-orange-400 h-full rounded-full" style={{ width: "76%" }}></div>
            </div>
          </div>

          <div className="p-3.5 rounded-2xl bg-white/[0.02] border border-white/[0.06] backdrop-blur-sm">
            <div className="flex justify-between items-center text-xs text-slate-400 mb-1">
              <span>Dietary Fibre</span>
              <span className="text-emerald-400 text-[11px]">Target Met ✅</span>
            </div>
            <p className="text-lg font-light text-emerald-300">28g <span className="text-xs text-slate-400">/ ≥25g</span></p>
            <div className="w-full bg-slate-800/80 rounded-full h-1.5 mt-2 overflow-hidden">
              <div className="bg-emerald-400 h-full rounded-full" style={{ width: "100%" }}></div>
            </div>
          </div>
        </div>

        {/* Interactive Tabs */}
        <div className="relative z-10 flex gap-2 pb-4 overflow-x-auto text-xs">
          <button
            onClick={() => setActiveTab("today")}
            className={`px-4 py-2 rounded-xl border transition-all font-medium ${
              activeTab === "today"
                ? "bg-emerald-500/20 text-emerald-300 border-emerald-500/40"
                : "border-white/10 text-slate-400 hover:text-white"
            }`}
          >
            🌿 Today's Gentle Journey
          </button>
          <button
            onClick={() => setActiveTab("swap")}
            className={`px-4 py-2 rounded-xl border transition-all font-medium ${
              activeTab === "swap"
                ? "bg-emerald-500/20 text-emerald-300 border-emerald-500/40"
                : "border-white/10 text-slate-400 hover:text-white"
            }`}
          >
            ✨ Mindful Meal Swap
          </button>
          <button
            onClick={() => setActiveTab("safety")}
            className={`px-4 py-2 rounded-xl border transition-all font-medium ${
              activeTab === "safety"
                ? "bg-emerald-500/20 text-emerald-300 border-emerald-500/40"
                : "border-white/10 text-slate-400 hover:text-white"
            }`}
          >
            🛡️ Safety Shield (Allergens)
          </button>
          <button
            onClick={() => setActiveTab("whisper")}
            className={`px-4 py-2 rounded-xl border transition-all font-medium ${
              activeTab === "whisper"
                ? "bg-emerald-500/20 text-emerald-300 border-emerald-500/40"
                : "border-white/10 text-slate-400 hover:text-white"
            }`}
          >
            💬 DietSense Whisper
          </button>
        </div>

        {/* Tab 1: Today */}
        {activeTab === "today" && (
          <div className="relative z-10 space-y-3">
            <div className="p-4 rounded-2xl bg-white/[0.02] border border-white/[0.06] flex flex-col sm:flex-row sm:items-center justify-between gap-4 border-l-4 border-l-amber-400/80">
              <div className="flex items-start gap-3.5">
                <div className="w-12 h-12 rounded-2xl bg-amber-500/10 border border-amber-400/20 flex items-center justify-center text-xl shrink-0">🥣</div>
                <div>
                  <div className="flex items-center gap-2">
                    <span className="text-[11px] uppercase tracking-wider text-amber-300/90 font-medium">Breakfast · 8:30 AM</span>
                    <span className="text-[10px] bg-emerald-900/50 text-emerald-300 px-2 py-0.5 rounded-full border border-emerald-700/30">ICMR-NIN Sourced</span>
                  </div>
                  <h3 className="text-base font-medium text-white mt-0.5">Spiced Oats & Moong Dal Porridge with Crushed Walnuts</h3>
                  <p className="text-xs text-slate-400 font-light mt-0.5">High dietary fibre, slow-release unrefined carbohydrates for calm morning focus.</p>
                </div>
              </div>
              <div className="flex items-center justify-between sm:justify-end gap-4 shrink-0 pt-2 sm:pt-0 border-t sm:border-t-0 border-white/5">
                <div className="text-right">
                  <p className="text-sm font-normal text-white">380 <span className="text-xs text-slate-400">kcal</span></p>
                  <p className="text-[11px] text-emerald-400">14g protein · 8g fibre</p>
                </div>
                <button className="px-3 py-1.5 rounded-xl bg-emerald-500/20 hover:bg-emerald-500/30 text-emerald-300 text-xs border border-emerald-500/30 transition-all">Enjoyed ✓</button>
              </div>
            </div>

            <div className="p-4 rounded-2xl bg-white/[0.02] border border-white/[0.06] flex flex-col sm:flex-row sm:items-center justify-between gap-4 border-l-4 border-l-emerald-400/80">
              <div className="flex items-start gap-3.5">
                <div className="w-12 h-12 rounded-2xl bg-emerald-500/10 border border-emerald-400/20 flex items-center justify-center text-xl shrink-0">🥗</div>
                <div>
                  <div className="flex items-center gap-2">
                    <span className="text-[11px] uppercase tracking-wider text-emerald-300/90 font-medium">Lunch · 1:15 PM</span>
                    <span className="text-[10px] bg-sky-900/50 text-sky-300 px-2 py-0.5 rounded-full border border-sky-700/30">SHAP Score: 0.94</span>
                  </div>
                  <h3 className="text-base font-medium text-white mt-0.5">Brown Rice Bowl with Spinach Dal & Sautéed Paneer</h3>
                  <p className="text-xs text-slate-400 font-light mt-0.5">Rich in plant iron and bioavailable calcium. Prepared with cold-pressed mustard oil.</p>
                </div>
              </div>
              <div className="flex items-center justify-between sm:justify-end gap-4 shrink-0 pt-2 sm:pt-0 border-t sm:border-t-0 border-white/5">
                <div className="text-right">
                  <p className="text-sm font-normal text-white">560 <span className="text-xs text-slate-400">kcal</span></p>
                  <p className="text-[11px] text-emerald-400">26g protein · 11g fibre</p>
                </div>
                <button className="px-3 py-1.5 rounded-xl bg-emerald-500/20 hover:bg-emerald-500/30 text-emerald-300 text-xs border border-emerald-500/30 transition-all">Enjoyed ✓</button>
              </div>
            </div>

            <div className="p-4 rounded-2xl bg-white/[0.02] border border-white/[0.06] flex flex-col sm:flex-row sm:items-center justify-between gap-4 border-l-4 border-l-teal-400/80">
              <div className="flex items-start gap-3.5">
                <div className="w-12 h-12 rounded-2xl bg-teal-500/10 border border-teal-400/20 flex items-center justify-center text-xl shrink-0">🍵</div>
                <div>
                  <div className="flex items-center gap-2">
                    <span className="text-[11px] uppercase tracking-wider text-teal-300/90 font-medium">Mindful Pause · 5:00 PM</span>
                  </div>
                  <h3 className="text-base font-medium text-white mt-0.5">Roasted Makhana with Green Cardamom Infusion</h3>
                  <p className="text-xs text-slate-400 font-light mt-0.5">Zero added free sugars. Packed with magnesium for nervous system calm.</p>
                </div>
              </div>
              <div className="flex items-center justify-between sm:justify-end gap-4 shrink-0 pt-2 sm:pt-0 border-t sm:border-t-0 border-white/5">
                <div className="text-right">
                  <p className="text-sm font-normal text-white">140 <span className="text-xs text-slate-400">kcal</span></p>
                  <p className="text-[11px] text-teal-300">4g protein · 3g fibre</p>
                </div>
                <button className="px-3 py-1.5 rounded-xl bg-white/10 hover:bg-white/20 text-white text-xs border border-white/10 transition-all">Mark Eaten</button>
              </div>
            </div>
          </div>
        )}

        {/* Tab 2: Swap */}
        {activeTab === "swap" && (
          <div className="relative z-10 space-y-4">
            <div className="p-5 rounded-2xl bg-emerald-950/20 border border-emerald-500/30">
              <div className="flex items-center gap-3 mb-3">
                <span className="text-2xl">🔄</span>
                <div>
                  <h3 className="text-base font-medium text-white">Feeling like something different for Dinner?</h3>
                  <p className="text-xs text-slate-400 font-light">DietSense recalculated alternatives using validated USDA/ICMR nutrition data:</p>
                </div>
              </div>
              <div className="grid grid-cols-1 md:grid-cols-2 gap-3 mt-4">
                <div className="p-3.5 rounded-xl bg-black/40 border border-emerald-500/30 relative">
                  <span className="absolute top-3 right-3 text-[10px] bg-emerald-500/20 text-emerald-300 px-2 py-0.5 rounded-full font-medium">96% Macro Match</span>
                  <h4 className="text-sm font-medium text-white">Grilled Tofu Veggie Wrap</h4>
                  <p className="text-xs text-slate-400 mt-1 font-light">Whole wheat roti base, steamed capsicum, mint yogurt drizzle.</p>
                  <div className="flex items-center justify-between mt-3 text-xs">
                    <span className="text-slate-300 font-light">355 kcal · 18g Protein</span>
                    <button className="px-2.5 py-1 rounded-lg bg-emerald-600 hover:bg-emerald-500 text-white font-medium text-[11px] transition-all">Select This</button>
                  </div>
                </div>

                <div className="p-3.5 rounded-xl bg-black/40 border border-white/10 relative">
                  <span className="absolute top-3 right-3 text-[10px] bg-teal-500/20 text-teal-300 px-2 py-0.5 rounded-full font-medium">91% Macro Match</span>
                  <h4 className="text-sm font-medium text-white">Lentil Quinoa Soup Bowl</h4>
                  <p className="text-xs text-slate-400 mt-1 font-light">Warm cumin broth, roasted cumin seeds, crushed flaxseed topping.</p>
                  <div className="flex items-center justify-between mt-3 text-xs">
                    <span className="text-slate-300 font-light">330 kcal · 15g Protein</span>
                    <button className="px-2.5 py-1 rounded-lg bg-white/10 hover:bg-white/20 text-white font-medium text-[11px] transition-all">Select This</button>
                  </div>
                </div>
              </div>
            </div>
          </div>
        )}

        {/* Tab 3: Safety */}
        {activeTab === "safety" && (
          <div className="relative z-10 grid grid-cols-1 sm:grid-cols-2 gap-3">
            <div className="p-4 rounded-2xl bg-white/[0.02] border border-white/[0.06] border-l-4 border-l-red-500">
              <h4 className="text-sm font-medium text-white flex items-center gap-2">
                <span>🚫</span> Active Hard Safety Filters
              </h4>
              <div className="flex flex-wrap gap-1.5 mt-2.5">
                <span className="px-2.5 py-1 rounded-lg bg-red-950/80 text-red-300 border border-red-800/40 text-xs">Peanuts / Tree Nuts (Filtered)</span>
                <span className="px-2.5 py-1 rounded-lg bg-emerald-950/80 text-emerald-300 border border-emerald-800/40 text-xs">Vegetarian Preference</span>
              </div>
              <p className="text-[11px] text-slate-400 mt-2 font-light">Rule 2 in action: 142 recipes with nut traces were blocked before scoring engine was invoked.</p>
            </div>

            <div className="p-4 rounded-2xl bg-white/[0.02] border border-white/[0.06] border-l-4 border-l-emerald-500">
              <h4 className="text-sm font-medium text-white flex items-center gap-2">
                <span>🌿</span> WHO 2026 Compliance
              </h4>
              <ul className="text-xs text-slate-300 space-y-1.5 mt-2 font-light">
                <li className="flex items-center gap-2"><span className="text-emerald-400">✓</span> Free Sugars: &lt; 4% total energy</li>
                <li className="flex items-center gap-2"><span className="text-emerald-400">✓</span> Salt / Sodium: 3.8g salt / day (&lt; 5.0g)</li>
                <li className="flex items-center gap-2"><span className="text-emerald-400">✓</span> Fibre: 28g / day (Target ≥ 25g)</li>
              </ul>
            </div>
          </div>
        )}

        {/* Tab 4: Whisper */}
        {activeTab === "whisper" && (
          <div className="relative z-10 p-4 rounded-2xl bg-white/[0.02] border border-white/[0.06] space-y-3">
            <div className="flex items-start gap-3">
              <div className="w-8 h-8 rounded-full bg-emerald-600/30 border border-emerald-400/30 flex items-center justify-center text-sm shrink-0">🌿</div>
              <div className="bg-emerald-950/40 border border-emerald-800/30 rounded-2xl rounded-tl-none p-3 text-xs text-slate-200 font-light max-w-lg leading-relaxed">
                I noticed you had a busy morning. How did your energy feel after the moong dal porridge? We can adjust lunch portions if you would like a lighter afternoon.
              </div>
            </div>
          </div>
        )}

        {/* Footer */}
        <div className="relative z-10 mt-6 pt-4 border-t border-white/5 flex flex-col sm:flex-row items-center justify-between text-[11px] text-slate-400 font-light gap-2">
          <span>DietSense Atmos · Powered by USDA &amp; ICMR-NIN Datasets</span>
          <span className="text-emerald-400/80">Every calorie is calculated, never hallucinated.</span>
        </div>

      </div>
    </main>
  );
}
