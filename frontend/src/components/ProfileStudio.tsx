import React from "react";
import { GoalType, Gender, MealFrequency, EffortLevel } from "@/types";
import { ActiveSlotsMap } from "@/lib/nutrition";

interface ProfileStudioProps {
  isSoloCook: boolean;
  setIsSoloCook: (val: boolean) => void;
  mealFrequency: MealFrequency;
  applyMealFrequency: (freq: MealFrequency) => void;
  activeSlots: ActiveSlotsMap;
  toggleSlot: (slot: keyof ActiveSlotsMap) => void;
  weekdayBreakfastEffort: EffortLevel;
  setWeekdayBreakfastEffort: (effort: EffortLevel) => void;
  weekdayLunchEffort: EffortLevel;
  setWeekdayLunchEffort: (effort: EffortLevel) => void;
  goal: GoalType;
  setGoal: (g: GoalType) => void;
  weight: number;
  setWeight: (w: number) => void;
  height: number;
  setHeight: (h: number) => void;
  age: number;
  setAge: (a: number) => void;
  gender: Gender;
  setGender: (g: Gender) => void;
  activity: number;
  setActivity: (act: number) => void;
  bmr: number;
  tdee: number;
  targetCalories: number;
  adjText: string;
  carbsGrams: number;
  proteinGrams: number;
  fatGrams: number;
}

export const ProfileStudio: React.FC<ProfileStudioProps> = ({
  isSoloCook,
  setIsSoloCook,
  mealFrequency,
  applyMealFrequency,
  activeSlots,
  toggleSlot,
  weekdayBreakfastEffort,
  setWeekdayBreakfastEffort,
  weekdayLunchEffort,
  setWeekdayLunchEffort,
  goal,
  setGoal,
  weight,
  setWeight,
  height,
  setHeight,
  age,
  setAge,
  gender,
  setGender,
  activity,
  setActivity,
  bmr,
  tdee,
  targetCalories,
  adjText,
  carbsGrams,
  proteinGrams,
  fatGrams,
}) => {
  return (
    <div className="relative z-10 space-y-4">
      {/* Solo Cook & Cooking Routine Settings Card */}
      <div className="rounded-2xl bg-white p-5 border border-[#e8ded3] shadow-sm space-y-4">
        <div className="flex items-center justify-between border-b border-slate-100 pb-3">
          <div>
            <h3 className="text-base font-serif text-[#421018] font-semibold flex items-center gap-2">
              <span>🍳</span> Solo Cooking &amp; Routine Customizer
            </h3>
            <p className="text-xs text-slate-500 mt-0.5">
              Living arrangement, daily meal count, aur weekday effort customize karo.
            </p>
          </div>
          <span className="text-xs bg-[#eff6ff] text-[#1d4ed8] px-2.5 py-1 rounded-full border border-[#bfdbfe] font-semibold">
            Solo Live Mode Active
          </span>
        </div>

        {/* Household & Cooking Mode */}
        <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
          <div className="p-4 rounded-xl bg-[#faf7f2] border border-[#e2d6c9] flex items-center justify-between">
            <div>
              <h4 className="text-xs font-bold text-[#421018]">Living &amp; Cooking Alone (Solo Mode)</h4>
              <p className="text-[11px] text-slate-600 mt-0.5">
                All recipes adjusted for 1 serving with zero leftover wastage.
              </p>
            </div>
            <input
              type="checkbox"
              checked={isSoloCook}
              onChange={(e) => setIsSoloCook(e.target.checked)}
              className="w-5 h-5 accent-[#581825] cursor-pointer"
            />
          </div>

          <div className="p-4 rounded-xl bg-[#faf7f2] border border-[#e2d6c9]">
            <label className="block text-xs font-bold text-[#421018] mb-1.5">Preset Daily Meal Routine</label>
            <select
              value={mealFrequency}
              onChange={(e) => applyMealFrequency(e.target.value as MealFrequency)}
              className="w-full bg-white border border-[#d8c8b8] rounded-lg px-2.5 py-1.5 text-xs text-slate-800 font-medium focus:outline-none"
            >
              <option value="2_meals">2 Meals · Intermittent Fasting (16:8 - Lunch + Dinner)</option>
              <option value="3_meals">3 Meals · Classic Routine (Breakfast, Lunch, Dinner)</option>
              <option value="4_meals">4 Meals · Active Day (Breakfast, Lunch, Evening Snack, Dinner)</option>
              <option value="5_meals">5 Meals · Metabolic 5-Stage (Early, BF, Lunch, Snack, Dinner)</option>
              <option value="custom">Custom Active Slots Selection</option>
            </select>
          </div>
        </div>

        {/* Slot Toggles */}
        <div>
          <label className="block text-xs font-semibold text-slate-700 uppercase tracking-wider mb-2">
            Active Meal Slots (Toggle which meals you eat)
          </label>
          <div className="grid grid-cols-2 sm:grid-cols-5 gap-2">
            {[
              { key: "early_morning", label: "☀️ Early Morning" },
              { key: "breakfast", label: "🥣 Breakfast" },
              { key: "lunch", label: "🍛 Lunch" },
              { key: "evening_snack", label: "🍵 Evening Snack" },
              { key: "dinner", label: "🍲 Dinner" },
            ].map((slot) => {
              const isActive = activeSlots[slot.key as keyof ActiveSlotsMap];
              return (
                <button
                  key={slot.key}
                  onClick={() => toggleSlot(slot.key as keyof ActiveSlotsMap)}
                  className={`p-2.5 rounded-xl border text-xs font-semibold transition-all text-center flex flex-col items-center justify-center gap-1 ${
                    isActive
                      ? "border-[#1d4ed8] bg-[#eff6ff] text-[#1d4ed8]"
                      : "border-slate-200 bg-white text-slate-400 hover:border-slate-300"
                  }`}
                >
                  <span>{slot.label}</span>
                  <span className="text-[10px] font-normal">{isActive ? "✓ Included" : "✕ Skipped"}</span>
                </button>
              );
            })}
          </div>
        </div>

        {/* Weekday Effort Preferences */}
        <div className="pt-2 border-t border-slate-100">
          <label className="block text-xs font-semibold text-slate-700 uppercase tracking-wider mb-2">
            Weekday Cooking Effort Preferences
          </label>
          <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
            <div className="p-3 rounded-xl bg-[#faf7f2] border border-[#e2d6c9]">
              <div className="flex justify-between items-center mb-1.5">
                <span className="text-xs font-bold text-[#421018]">Weekday Breakfast Effort:</span>
                <span className="text-[11px] font-semibold text-[#1d4ed8]">
                  {weekdayBreakfastEffort === "low" ? "⚡ Low Effort (<12m)" : "🍳 Moderate (~20m)"}
                </span>
              </div>
              <div className="flex gap-2">
                <button
                  onClick={() => setWeekdayBreakfastEffort("low")}
                  className={`flex-1 py-1.5 text-xs rounded-lg font-semibold border ${
                    weekdayBreakfastEffort === "low"
                      ? "bg-[#581825] text-white border-[#581825]"
                      : "bg-white text-slate-700 border-[#d8c8b8]"
                  }`}
                >
                  ⚡ Low Effort (&lt;12m)
                </button>
                <button
                  onClick={() => setWeekdayBreakfastEffort("moderate")}
                  className={`flex-1 py-1.5 text-xs rounded-lg font-semibold border ${
                    weekdayBreakfastEffort === "moderate"
                      ? "bg-[#581825] text-white border-[#581825]"
                      : "bg-white text-slate-700 border-[#d8c8b8]"
                  }`}
                >
                  🍳 Moderate (20m)
                </button>
              </div>
            </div>

            <div className="p-3 rounded-xl bg-[#faf7f2] border border-[#e2d6c9]">
              <div className="flex justify-between items-center mb-1.5">
                <span className="text-xs font-bold text-[#421018]">Weekday Lunch Effort:</span>
                <span className="text-[11px] font-semibold text-[#581825]">
                  {weekdayLunchEffort === "moderate" ? "🍳 Moderate (20-30m)" : "⏱️ Express 1-Pot"}
                </span>
              </div>
              <div className="flex gap-2">
                <button
                  onClick={() => setWeekdayLunchEffort("moderate")}
                  className={`flex-1 py-1.5 text-xs rounded-lg font-semibold border ${
                    weekdayLunchEffort === "moderate"
                      ? "bg-[#581825] text-white border-[#581825]"
                      : "bg-white text-slate-700 border-[#d8c8b8]"
                  }`}
                >
                  🍳 Moderate (20-30m)
                </button>
                <button
                  onClick={() => setWeekdayLunchEffort("low")}
                  className={`flex-1 py-1.5 text-xs rounded-lg font-semibold border ${
                    weekdayLunchEffort === "low"
                      ? "bg-[#581825] text-white border-[#581825]"
                      : "bg-white text-slate-700 border-[#d8c8b8]"
                  }`}
                >
                  ⏱️ Express 1-Pot
                </button>
              </div>
            </div>
          </div>
        </div>
      </div>

      {/* Biometrics & Calculation */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
        {/* Controls */}
        <div className="md:col-span-2 rounded-2xl bg-white p-5 border border-[#e8ded3] shadow-sm space-y-4">
          <h3 className="text-base font-serif text-[#421018] flex items-center justify-between">
            <span>Biometrics &amp; Activity</span>
            <span className="text-xs font-sans text-slate-400 font-normal">Mifflin-St Jeor</span>
          </h3>

          {/* Goal Selector */}
          <div>
            <label className="block text-xs font-semibold text-slate-700 uppercase tracking-wider mb-2">
              Target Goal
            </label>
            <div className="grid grid-cols-3 gap-2">
              <button
                onClick={() => setGoal("lose_weight")}
                className={`py-2.5 px-3 rounded-xl border-2 text-xs transition-all text-center ${
                  goal === "lose_weight"
                    ? "border-[#1d4ed8] bg-[#eff6ff] text-[#1d4ed8] font-bold"
                    : "border-[#d8c8b8] bg-white text-slate-700 font-medium"
                }`}
              >
                🔥 Cut (Fat Loss)<br />
                <span className="text-[10px] font-normal text-slate-500">-400 kcal deficit</span>
              </button>
              <button
                onClick={() => setGoal("maintain_weight")}
                className={`py-2.5 px-3 rounded-xl border-2 text-xs transition-all text-center ${
                  goal === "maintain_weight"
                    ? "border-[#1d4ed8] bg-[#eff6ff] text-[#1d4ed8] font-bold"
                    : "border-[#d8c8b8] bg-white text-slate-700 font-medium"
                }`}
              >
                ⚖️ Maintain<br />
                <span className="text-[10px] font-normal text-slate-500">TDEE Balance</span>
              </button>
              <button
                onClick={() => setGoal("gain_weight")}
                className={`py-2.5 px-3 rounded-xl border-2 text-xs transition-all text-center ${
                  goal === "gain_weight"
                    ? "border-[#1d4ed8] bg-[#eff6ff] text-[#1d4ed8] font-bold"
                    : "border-[#d8c8b8] bg-white text-slate-700 font-medium"
                }`}
              >
                💪 Lean Gain<br />
                <span className="text-[10px] font-normal text-slate-500">+300 kcal surplus</span>
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
                className="w-full cursor-pointer accent-[#581825]"
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
                className="w-full cursor-pointer accent-[#581825]"
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
                className="w-full cursor-pointer accent-[#581825]"
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
                <option value="male">Male</option>
                <option value="female">Female</option>
              </select>
            </div>
          </div>

          {/* Activity */}
          <div>
            <label className="block text-xs font-semibold text-slate-700 uppercase tracking-wider mb-1.5">
              Daily Activity Level
            </label>
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
              <h4 className="text-xs uppercase tracking-wider font-semibold text-slate-500">
                Calculated Metabolism
              </h4>
            </div>
            <p className="text-xl font-serif text-[#421018] font-bold">
              {bmr.toLocaleString()} kcal{" "}
              <span className="text-xs font-sans text-slate-400 font-normal">BMR</span>
            </p>
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
                <span className="text-base font-serif font-bold text-[#421018]">
                  {targetCalories.toLocaleString()} kcal
                </span>
              </div>
            </div>
          </div>

          <div className="pt-3 border-t border-slate-100 space-y-1.5 text-xs">
            <p className="font-semibold text-slate-700 text-[11px] uppercase tracking-wider">
              Suggested Macro Split (WHO)
            </p>
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
  );
};
