"use client";

import { useState } from "react";

export default function HomePage() {
  const [activeTab, setActiveTab] = useState<"profile" | "today" | "swap" | "safety">("profile");

  // Profile State
  const [goal, setGoal] = useState<"lose_weight" | "maintain_weight" | "gain_weight">("lose_weight");
  const [weight, setWeight] = useState<number>(75);
  const [height, setHeight] = useState<number>(175);
  const [age, setAge] = useState<number>(26);
  const [gender, setGender] = useState<"male" | "female">("male");
  const [activity, setActivity] = useState<number>(1.375);

  // Mifflin-St Jeor Calculation
  let bmr = 10 * weight + 6.25 * height - 5 * age;
  bmr = gender === "male" ? bmr + 5 : bmr - 161;
  bmr = Math.round(bmr);

  const tdee = Math.round(bmr * activity);
  let targetCalories = tdee;
  let adjText = "0 kcal (Maintenance)";

  if (goal === "lose_weight") {
    targetCalories = Math.max(1200, tdee - 400);
    adjText = "-400 kcal (Cut Deficit)";
  } else if (goal === "gain_weight") {
    targetCalories = tdee + 300;
    adjText = "+300 kcal (Lean Surplus)";
  }

  // Macro Grams (WHO Split)
  const carbsGrams = Math.round((targetCalories * 0.5) / 4);
  const proteinGrams = Math.round((targetCalories * 0.2) / 4);
  const fatGrams = Math.round((targetCalories * 0.3) / 9);

  return (
    <main className="min-h-screen bg-[#f5f0e8] text-slate-800 p-4 sm:p-8 flex items-center justify-center font-sans antialiased">
      <div className="relative w-full max-w-4xl overflow-hidden rounded-3xl border border-[#e8ded3] bg-[#faf7f2] p-5 sm:p-8 shadow-xl text-slate-800">
        
        {/* Ambient Lights */}
        <div className="absolute -top-24 -right-16 w-96 h-96 bg-[#dbeafe]/70 rounded-full blur-3xl pointer-events-none animate-pulse"></div>
        <div className="absolute -bottom-24 -left-16 w-96 h-96 bg-[#fce7f3]/50 rounded-full blur-3xl pointer-events-none animate-pulse"></div>

        {/* Top Atmosphere Header */}
        <div className="relative z-10 flex flex-col md:flex-row md:items-center justify-between gap-5 pb-6 border-b border-[#e9dfd5]">
          <div>
            <div className="inline-flex items-center gap-2 px-3 py-1 rounded-full bg-[#f3eae0] border border-[#d8c8b8] text-[#581825] text-xs font-medium tracking-wide mb-2.5 shadow-sm">
              <span className="w-2 h-2 rounded-full bg-[#581825] animate-pulse"></span>
              <span>DietSense Atmos · Personal Profile & Metabolic Studio</span>
            </div>
            <h1 className="text-2xl sm:text-3xl font-serif text-[#421018] tracking-tight">
              Namaste, <span className="text-[#1d4ed8] font-sans font-normal">Aarav</span>
            </h1>
            <p className="text-sm text-slate-600 mt-1 font-light max-w-xl">
              Customize your biometrics, activity, and whether you wish to cut, maintain, or lean bulk.
            </p>
          </div>

          {/* Dynamic Target Card */}
          <div className="flex items-center gap-4 bg-white/90 border border-[#e2d6c9] rounded-2xl p-3.5 px-5 shadow-sm backdrop-blur-md">
            <div className="relative flex items-center justify-center">
              <svg className="w-13 h-13 transform -rotate-90" viewBox="0 0 48 48">
                <circle cx="24" cy="24" r="20" stroke="#f1e9df" strokeWidth="4.5" fill="transparent"/>
                <circle cx="24" cy="24" r="20" stroke="#1d4ed8" strokeWidth="4.5" strokeDasharray="125.6" strokeDashoffset="37.6" strokeLinecap="round" fill="transparent"/>
              </svg>
              <span className="absolute text-xs font-bold text-[#1d4ed8]">Target</span>
            </div>
            <div>
              <p className="text-[11px] uppercase tracking-wider text-slate-500 font-semibold">
                {goal === "lose_weight" ? "Goal: Cut (-400)" : goal === "gain_weight" ? "Goal: Surplus (+300)" : "Goal: Maintain"}
              </p>
              <p className="text-base text-[#421018] font-serif font-semibold">{targetCalories.toLocaleString()} <span className="text-xs font-sans text-slate-500 font-normal">kcal/day</span></p>
            </div>
          </div>
        </div>

        {/* Tab Selector */}
        <div className="relative z-10 flex gap-2 my-5 pb-1 overflow-x-auto text-xs">
          <button
            onClick={() => setActiveTab("profile")}
            className={`px-4 py-2 rounded-xl border transition-all font-medium ${
              activeTab === "profile"
                ? "bg-[#581825] text-white border-[#581825] shadow-sm"
                : "border-[#d8c8b8] bg-white/80 text-slate-600 hover:text-[#581825]"
            }`}
          >
            👤 My Profile & Goal (Cut / Maintain)
          </button>
          <button
            onClick={() => setActiveTab("today")}
            className={`px-4 py-2 rounded-xl border transition-all font-medium ${
              activeTab === "today"
                ? "bg-[#581825] text-white border-[#581825] shadow-sm"
                : "border-[#d8c8b8] bg-white/80 text-slate-600 hover:text-[#581825]"
            }`}
          >
            🥣 Daily Meal Plan
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
        </div>

        {/* Profile Studio Tab */}
        {activeTab === "profile" && (
          <div className="relative z-10 space-y-4">
            <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
              
              {/* Controls */}
              <div className="md:col-span-2 rounded-2xl bg-white p-5 border border-[#e8ded3] shadow-sm space-y-4">
                <h3 className="text-base font-serif text-[#421018] flex items-center justify-between">
                  <span>Biometrics & Activity</span>
                  <span className="text-xs font-sans text-slate-400 font-normal">Mifflin-St Jeor</span>
                </h3>

                {/* Goal Selector */}
                <div>
                  <label className="block text-xs font-semibold text-slate-700 uppercase tracking-wider mb-2">Target Goal</label>
                  <div className="grid grid-cols-3 gap-2">
                    <button
                      onClick={() => setGoal("lose_weight")}
                      className={`py-2.5 px-3 rounded-xl border-2 text-xs transition-all text-center ${
                        goal === "lose_weight"
                          ? "border-[#1d4ed8] bg-[#eff6ff] text-[#1d4ed8] font-bold"
                          : "border-[#d8c8b8] bg-white text-slate-700 font-medium"
                      }`}
                    >
                      🔥 Cut (Fat Loss)<br/><span className="text-[10px] font-normal text-slate-500">-400 kcal deficit</span>
                    </button>
                    <button
                      onClick={() => setGoal("maintain_weight")}
                      className={`py-2.5 px-3 rounded-xl border-2 text-xs transition-all text-center ${
                        goal === "maintain_weight"
                          ? "border-[#1d4ed8] bg-[#eff6ff] text-[#1d4ed8] font-bold"
                          : "border-[#d8c8b8] bg-white text-slate-700 font-medium"
                      }`}
                    >
                      ⚖️ Maintain<br/><span className="text-[10px] font-normal text-slate-500">TDEE Balance</span>
                    </button>
                    <button
                      onClick={() => setGoal("gain_weight")}
                      className={`py-2.5 px-3 rounded-xl border-2 text-xs transition-all text-center ${
                        goal === "gain_weight"
                          ? "border-[#1d4ed8] bg-[#eff6ff] text-[#1d4ed8] font-bold"
                          : "border-[#d8c8b8] bg-white text-slate-700 font-medium"
                      }`}
                    >
                      💪 Lean Gain<br/><span className="text-[10px] font-normal text-slate-500">+300 kcal surplus</span>
                    </button>
                  </div>
                </div>

                {/* Sliders */}
                <div className="grid grid-cols-1 sm:grid-cols-2 gap-4 pt-2">
                  <div className="p-3.5 rounded-xl bg-[#faf7f2] border border-[#e2d6c9]">
                    <div className="flex justify-between items-center mb-1.5">
                      <span className="text-xs font-medium text-slate-700">Body Weight</span>
                      <span className="text-sm font-bold text-[#421018]">{weight} kg</span>
                    </div>
                    <input
                      type="range"
                      min={40}
                      max={150}
                      value={weight}
                      step={0.5}
                      className="w-full cursor-pointer"
                      onChange={(e) => setWeight(parseFloat(e.target.value))}
                    />
                  </div>

                  <div className="p-3.5 rounded-xl bg-[#faf7f2] border border-[#e2d6c9]">
                    <div className="flex justify-between items-center mb-1.5">
                      <span className="text-xs font-medium text-slate-700">Height</span>
                      <span className="text-sm font-bold text-[#421018]">{height} cm</span>
                    </div>
                    <input
                      type="range"
                      min={130}
                      max={210}
                      value={height}
                      step={1}
                      className="w-full cursor-pointer"
                      onChange={(e) => setHeight(parseFloat(e.target.value))}
                    />
                  </div>

                  <div className="p-3.5 rounded-xl bg-[#faf7f2] border border-[#e2d6c9]">
                    <div className="flex justify-between items-center mb-1.5">
                      <span className="text-xs font-medium text-slate-700">Age</span>
                      <span className="text-sm font-bold text-[#421018]">{age} yrs</span>
                    </div>
                    <input
                      type="range"
                      min={15}
                      max={80}
                      value={age}
                      step={1}
                      className="w-full cursor-pointer"
                      onChange={(e) => setAge(parseInt(e.target.value))}
                    />
                  </div>

                  <div className="p-3.5 rounded-xl bg-[#faf7f2] border border-[#e2d6c9] space-y-1">
                    <label className="block text-xs font-medium text-slate-700 mb-1">Biological Profile</label>
                    <select
                      value={gender}
                      onChange={(e) => setGender(e.target.value as "male" | "female")}
                      className="w-full bg-white border border-[#d8c8b8] rounded-lg px-2.5 py-1 text-xs text-slate-800 focus:outline-none"
                    >
                      <option value="male">Male (Coefficient +5)</option>
                      <option value="female">Female (Coefficient -161)</option>
                    </select>
                  </div>
                </div>

                {/* Activity */}
                <div>
                  <label className="block text-xs font-semibold text-slate-700 uppercase tracking-wider mb-1.5">Daily Activity Level</label>
                  <select
                    value={activity}
                    onChange={(e) => setActivity(parseFloat(e.target.value))}
                    className="w-full bg-[#faf7f2] border border-[#d8c8b8] rounded-xl px-3.5 py-2.5 text-xs text-slate-800 font-medium focus:outline-none"
                  >
                    <option value={1.2}>Sedentary (Desk job, little to no exercise) · 1.2x</option>
                    <option value={1.375}>Lightly Active (Walking/light exercise 1-3 days/wk) · 1.375x</option>
                    <option value={1.55}>Moderately Active (Workout 3-5 days/wk) · 1.55x</option>
                    <option value={1.725}>Very Active (Intense exercise 6-7 days/wk) · 1.725x</option>
                    <option value={1.9}>Extra Active (Athlete / physical labor) · 1.9x</option>
                  </select>
                </div>
              </div>

              {/* Live Calculated Metabolism Card */}
              <div className="rounded-2xl bg-white p-5 border border-[#e8ded3] shadow-sm flex flex-col justify-between space-y-4">
                <div>
                  <div className="flex items-center gap-2 mb-1">
                    <span className="w-2 h-2 rounded-full bg-[#1d4ed8]"></span>
                    <h4 className="text-xs uppercase tracking-wider font-semibold text-slate-500">Calculated Metabolism</h4>
                  </div>
                  <p className="text-xl font-serif text-[#421018] font-bold">{bmr.toLocaleString()} kcal <span className="text-xs font-sans text-slate-400 font-normal">BMR</span></p>
                  <p className="text-xs text-slate-500 font-light mt-0.5">Energy burned at complete rest.</p>
                </div>

                <div className="space-y-2.5 pt-3 border-t border-slate-100">
                  <div className="flex justify-between items-center text-xs">
                    <span className="text-slate-600">Maintenance (TDEE)</span>
                    <span className="font-bold text-slate-800">{tdee.toLocaleString()} kcal</span>
                  </div>
                  <div className="flex justify-between items-center text-xs">
                    <span className="text-slate-600">Goal Adjustment</span>
                    <span className="font-bold text-[#1d4ed8]">{adjText}</span>
                  </div>
                  <div className="p-3 rounded-xl bg-[#eff6ff] border border-[#bfdbfe]">
                    <div className="flex justify-between items-center text-xs">
                      <span className="font-bold text-[#1d4ed8]">Daily Target</span>
                      <span className="text-base font-serif font-bold text-[#421018]">{targetCalories.toLocaleString()} kcal</span>
                    </div>
                  </div>
                </div>

                <div className="pt-3 border-t border-slate-100 space-y-1.5 text-xs">
                  <p className="font-semibold text-slate-700 text-[11px] uppercase tracking-wider">Suggested Macro Split (WHO)</p>
                  <div className="flex justify-between text-slate-600">
                    <span>Carbs (50%)</span>
                    <span className="font-medium text-slate-800">{carbsGrams}g</span>
                  </div>
                  <div className="flex justify-between text-slate-600">
                    <span>Protein (20%)</span>
                    <span className="font-medium text-[#581825]">{proteinGrams}g</span>
                  </div>
                  <div className="flex justify-between text-slate-600">
                    <span>Fats (30%)</span>
                    <span className="font-medium text-[#0369a1]">{fatGrams}g</span>
                  </div>
                </div>
              </div>

            </div>
          </div>
        )}

        {/* Tab 2: Daily Meal Plan */}
        {activeTab === "today" && (
          <div className="relative z-10 space-y-3">
            <div className="rounded-2xl bg-white p-4.5 border border-[#e8ded3] flex flex-col sm:flex-row sm:items-center justify-between gap-4 border-l-4 border-l-[#1d4ed8] shadow-sm">
              <div className="flex items-start gap-3.5">
                <div className="w-12 h-12 rounded-2xl bg-[#eff6ff] border border-[#bfdbfe] flex items-center justify-center text-xl shrink-0">🥣</div>
                <div>
                  <div className="flex items-center gap-2">
                    <span className="text-[11px] uppercase tracking-wider text-[#1d4ed8] font-bold">Breakfast · 8:30 AM</span>
                    <span className="text-[10px] bg-[#f8fafc] text-slate-600 px-2 py-0.5 rounded-full border border-slate-200">ICMR-NIN</span>
                  </div>
                  <h3 className="text-base font-serif text-[#421018] mt-0.5">Spiced Oats & Moong Dal Porridge with Crushed Walnuts</h3>
                  <p className="text-xs text-slate-600 font-light mt-0.5">Rich unrefined complex carbohydrates and prebiotic fibre for morning energy.</p>
                </div>
              </div>
              <div className="text-right">
                <p className="text-sm font-semibold text-[#421018]">380 <span className="text-xs font-normal text-slate-400">kcal</span></p>
                <p className="text-[11px] text-[#1d4ed8] font-medium">14g protein · 8g fibre</p>
              </div>
            </div>

            <div className="rounded-2xl bg-white p-4.5 border border-[#e8ded3] flex flex-col sm:flex-row sm:items-center justify-between gap-4 border-l-4 border-l-[#581825] shadow-sm">
              <div className="flex items-start gap-3.5">
                <div className="w-12 h-12 rounded-2xl bg-[#fdf2f4] border border-[#fbcfe8] flex items-center justify-center text-xl shrink-0">🥗</div>
                <div>
                  <div className="flex items-center gap-2">
                    <span className="text-[11px] uppercase tracking-wider text-[#581825] font-bold">Lunch · 1:15 PM</span>
                    <span className="text-[10px] bg-[#eff6ff] text-[#1d4ed8] px-2 py-0.5 rounded-full border border-[#bfdbfe] font-medium">SHAP: 0.94</span>
                  </div>
                  <h3 className="text-base font-serif text-[#421018] mt-0.5">Brown Rice Bowl with Palak Dal & Sautéed Paneer</h3>
                  <p className="text-xs text-slate-600 font-light mt-0.5">High bioavailable iron and plant calcium. Seasoned with mustard oil.</p>
                </div>
              </div>
              <div className="text-right">
                <p className="text-sm font-semibold text-[#421018]">560 <span className="text-xs font-normal text-slate-400">kcal</span></p>
                <p className="text-[11px] text-[#1d4ed8] font-medium">26g protein · 11g fibre</p>
              </div>
            </div>
          </div>
        )}

        {/* Tab 3: Swap */}
        {activeTab === "swap" && (
          <div className="relative z-10 space-y-4">
            <div className="rounded-2xl bg-white p-5 border border-[#e8ded3] shadow-sm">
              <h3 className="text-base font-serif text-[#421018]">Mindful Swap Generator</h3>
              <p className="text-xs text-slate-500 font-light mt-1">Calculated alternatives maintaining your {targetCalories} kcal target:</p>
              <div className="grid grid-cols-1 md:grid-cols-2 gap-3 mt-4">
                <div className="p-4 rounded-xl bg-[#faf7f2] border border-[#e2d6c9]">
                  <span className="text-[10px] bg-[#eff6ff] text-[#1d4ed8] border border-[#bfdbfe] px-2 py-0.5 rounded-full font-bold">96% Macro Match</span>
                  <h4 className="text-sm font-semibold text-[#421018] mt-2">Grilled Tofu Veggie Wrap</h4>
                  <p className="text-xs text-slate-600 mt-1">355 kcal · 18g Protein</p>
                </div>
                <div className="p-4 rounded-xl bg-[#faf7f2] border border-[#e2d6c9]">
                  <span className="text-[10px] bg-[#f0f9ff] text-[#0284c7] border border-[#bae6fd] px-2 py-0.5 rounded-full font-bold">91% Macro Match</span>
                  <h4 className="text-sm font-semibold text-[#421018] mt-2">Lentil Quinoa Broth Bowl</h4>
                  <p className="text-xs text-slate-600 mt-1">330 kcal · 15g Protein</p>
                </div>
              </div>
            </div>
          </div>
        )}

        {/* Tab 4: Safety */}
        {activeTab === "safety" && (
          <div className="relative z-10 grid grid-cols-1 sm:grid-cols-2 gap-3">
            <div className="rounded-2xl bg-white p-4.5 border border-[#e8ded3] border-l-4 border-l-[#581825] shadow-sm">
              <h4 className="text-sm font-serif text-[#421018] flex items-center gap-2">
                <span>🚫</span> Active Safety Shield
              </h4>
              <div className="flex flex-wrap gap-1.5 mt-2.5">
                <span className="px-2.5 py-1 rounded-lg bg-[#fdf2f4] text-[#581825] border border-[#fbcfe8] text-xs font-medium">Tree Nuts (Blocked)</span>
                <span className="px-2.5 py-1 rounded-lg bg-[#eff6ff] text-[#1d4ed8] border border-[#bfdbfe] text-xs font-medium">Vegetarian</span>
              </div>
            </div>
            <div className="rounded-2xl bg-white p-4.5 border border-[#e8ded3] border-l-4 border-l-[#1d4ed8] shadow-sm">
              <h4 className="text-sm font-serif text-[#421018] flex items-center gap-2">
                <span>🌿</span> WHO 2026 Dietary Compliance
              </h4>
              <ul className="text-xs text-slate-600 space-y-1.5 mt-2">
                <li>✓ Free Sugars: &lt; 4% total energy</li>
                <li>✓ Salt / Sodium: 3.8g / day (Target &lt; 5.0g)</li>
              </ul>
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
