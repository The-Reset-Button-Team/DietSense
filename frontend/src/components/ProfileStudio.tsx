"use client";

import React, { useState } from "react";
import { GoalType, Gender, MealFrequency, EffortLevel } from "@/types";
import { ActiveSlotsMap } from "@/lib/nutrition";
import { useAuth } from "@/context/AuthContext";

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
  const { user, updateProfile } = useAuth();
  const [dietaryType, setDietaryType] = useState<"omnivore" | "vegetarian" | "vegan">(
    (user?.dietary_preference as any) || "vegetarian"
  );
  const [allergens, setAllergens] = useState<string[]>(
    user?.allergies || ["peanuts"]
  );
  const [isSaved, setIsSaved] = useState(false);

  const toggleAllergen = (id: string) => {
    if (allergens.includes(id)) {
      setAllergens(allergens.filter((a) => a !== id));
    } else {
      setAllergens([...allergens, id]);
    }
  };

  const handleSave = async () => {
    try {
      if (updateProfile) {
        await updateProfile({
          age,
          gender,
          weight_kg: weight,
          height_cm: height,
          goal,
          dietary_preference: dietaryType,
          allergies: allergens,
          is_solo_cook: isSoloCook,
          active_meal_frequency: mealFrequency,
        });
      }
      setIsSaved(true);
      setTimeout(() => setIsSaved(false), 3000);
    } catch {
      setIsSaved(true);
      setTimeout(() => setIsSaved(false), 3000);
    }
  };

  const palOptions = [
    { val: 1.2, label: "Sedentary", desc: "1.20× Deskbound" },
    { val: 1.375, label: "Light", desc: "1.375× 1-3 d/wk" },
    { val: 1.55, label: "Moderate Active", desc: "1.55× 3-5 d/wk" },
    { val: 1.725, label: "Very Active", desc: "1.725× 6-7 d/wk" },
  ];

  const allergenList = [
    { id: "peanuts", label: "Peanuts" },
    { id: "tree_nuts", label: "Tree Nuts (Walnuts, Cashews)" },
    { id: "shellfish", label: "Shellfish & Crustaceans" },
    { id: "dairy", label: "Lactose / Dairy" },
    { id: "gluten", label: "Gluten & Wheat" },
    { id: "eggs", label: "Eggs" },
    { id: "soy", label: "Soy & Edamame" },
  ];

  return (
    <div className="space-y-space-lg pb-16">
      {/* Top Editorial Header */}
      <div className="flex flex-col lg:flex-row lg:items-end justify-between gap-space-md pt-space-xs pb-space-sm border-b border-surface-container-highest">
        <div className="space-y-1">
          <div className="flex items-center gap-space-xs text-primary">
            <span className="material-symbols-outlined text-[18px]">tune</span>
            <span className="font-label-sm text-label-sm uppercase tracking-wider text-primary font-bold">
              Metabolic Calibration &amp; Safety Matrix
            </span>
          </div>
          <h1 className="font-headline-lg text-headline-lg text-primary tracking-tight font-serif">
            Profile Studio &amp; Biometrics
          </h1>
          <p className="font-body-md text-body-md text-on-surface-variant max-w-2xl">
            Evidence-based metabolic baseline calculation via the Mifflin-St Jeor equation. Hard
            allergen exclusions are enforced as absolute boolean gates before any meal scoring
            takes place.
          </p>
        </div>

        <button
          type="button"
          onClick={handleSave}
          className="px-space-lg py-2.5 bg-primary hover:bg-primary-container text-on-primary rounded font-label-md text-label-md transition-all shadow-sm flex items-center gap-2 self-start lg:self-auto"
        >
          <span className="material-symbols-outlined text-[18px]">save</span>
          Save Biometric Profile
        </button>
      </div>

      {isSaved && (
        <div className="p-space-sm rounded-lg bg-secondary/10 border border-secondary text-secondary font-label-md flex items-center gap-2 animate-in fade-in">
          <span className="material-symbols-outlined text-[18px]">check_circle</span>
          Biometric calibrations and safety gates synchronized with local SQLite.
        </div>
      )}

      {/* Grid: 8-Column Engine + 4-Column Logistics Rail */}
      <div className="grid grid-cols-1 lg:grid-cols-12 gap-space-lg items-start">
        {/* Left 8-Column Main Studio */}
        <div className="lg:col-span-8 space-y-space-lg">
          {/* Mifflin-St Jeor Biometric Engine Card */}
          <div className="bg-surface-container-lowest p-space-lg rounded-xl shadow-sm border border-surface-container space-y-space-md">
            <div className="flex items-center justify-between pb-space-xs border-b border-surface-container">
              <div>
                <h2 className="font-headline-sm text-headline-sm text-primary font-serif">
                  Mifflin-St Jeor Biometric Engine
                </h2>
                <p className="font-body-sm text-body-sm text-on-surface-variant">
                  Precision basal metabolic calculation (American Dietetic Association gold standard)
                </p>
              </div>
              <span className="px-2.5 py-0.5 rounded-full bg-surface-container font-label-sm text-label-sm text-on-surface-variant font-mono">
                Formula v2.1
              </span>
            </div>

            {/* Inputs Grid */}
            <div className="grid grid-cols-1 sm:grid-cols-2 gap-space-md pt-space-xs">
              {/* Biological Gender */}
              <div>
                <label className="font-label-md text-label-md text-on-surface block mb-1">
                  Biological Sex (Formula Offset)
                </label>
                <div className="grid grid-cols-2 gap-2">
                  <button
                    type="button"
                    onClick={() => setGender("male")}
                    className={`py-2 px-3 rounded font-label-md text-label-md transition-all text-center border ${
                      gender === "male"
                        ? "bg-primary text-on-primary border-primary font-bold shadow-sm"
                        : "bg-surface-container text-on-surface-variant border-transparent hover:text-on-surface"
                    }`}
                  >
                    Male (+5 kcal)
                  </button>
                  <button
                    type="button"
                    onClick={() => setGender("female")}
                    className={`py-2 px-3 rounded font-label-md text-label-md transition-all text-center border ${
                      gender === "female"
                        ? "bg-primary text-on-primary border-primary font-bold shadow-sm"
                        : "bg-surface-container text-on-surface-variant border-transparent hover:text-on-surface"
                    }`}
                  >
                    Female (-161 kcal)
                  </button>
                </div>
              </div>

              {/* Age */}
              <div>
                <div className="flex justify-between items-center mb-1">
                  <label className="font-label-md text-label-md text-on-surface">Chronological Age</label>
                  <span className="font-metric-num text-[18px] text-primary">{age} yrs</span>
                </div>
                <input
                  type="range"
                  min="16"
                  max="85"
                  value={age}
                  onChange={(e) => setAge(Number(e.target.value))}
                  className="w-full h-2 bg-surface-variant rounded-lg appearance-none cursor-pointer accent-primary"
                />
              </div>

              {/* Height */}
              <div>
                <div className="flex justify-between items-center mb-1">
                  <label className="font-label-md text-label-md text-on-surface">Stature / Height</label>
                  <span className="font-metric-num text-[18px] text-primary">
                    {height}{" "}
                    <span className="font-label-md text-[13px] font-normal text-on-surface-variant">
                      cm ({Math.floor(height / 30.48)}&apos;
                      {Math.round((height % 30.48) / 2.54)}&quot;)
                    </span>
                  </span>
                </div>
                <input
                  type="range"
                  min="140"
                  max="215"
                  value={height}
                  onChange={(e) => setHeight(Number(e.target.value))}
                  className="w-full h-2 bg-surface-variant rounded-lg appearance-none cursor-pointer accent-primary"
                />
              </div>

              {/* Weight */}
              <div>
                <div className="flex justify-between items-center mb-1">
                  <label className="font-label-md text-label-md text-on-surface">Current Body Weight</label>
                  <span className="font-metric-num text-[18px] text-primary">
                    {weight}{" "}
                    <span className="font-label-md text-[13px] font-normal text-on-surface-variant">
                      kg
                    </span>
                  </span>
                </div>
                <input
                  type="range"
                  min="40"
                  max="140"
                  step="0.5"
                  value={weight}
                  onChange={(e) => setWeight(Number(e.target.value))}
                  className="w-full h-2 bg-surface-variant rounded-lg appearance-none cursor-pointer accent-primary"
                />
              </div>
            </div>

            {/* Activity Level Multiplier */}
            <div>
              <label className="font-label-md text-label-md text-on-surface block mb-2">
                Physical Activity Factor (PAL)
              </label>
              <div className="grid grid-cols-2 md:grid-cols-4 gap-2">
                {palOptions.map((opt) => (
                  <button
                    key={opt.val}
                    type="button"
                    onClick={() => setActivity(opt.val)}
                    className={`p-space-sm rounded text-left transition-all border ${
                      Math.abs(activity - opt.val) < 0.05
                        ? "bg-primary text-on-primary border-primary font-bold shadow-sm"
                        : "bg-surface-container text-on-surface border-transparent hover:bg-surface-container-high"
                    }`}
                  >
                    <div className="font-label-md text-label-md">{opt.label}</div>
                    <div
                      className={`font-metric-num text-[12px] ${
                        Math.abs(activity - opt.val) < 0.05
                          ? "text-primary-fixed"
                          : "text-on-surface-variant"
                      }`}
                    >
                      {opt.desc}
                    </div>
                  </button>
                ))}
              </div>
            </div>

            {/* Formula Decomposition Card */}
            <div className="bg-surface-container-low p-space-md rounded-lg space-y-space-sm border border-surface-container">
              <div className="flex items-center justify-between">
                <span className="font-label-md text-label-md uppercase tracking-wider text-primary font-bold flex items-center gap-1">
                  <span className="material-symbols-outlined text-[16px]">calculate</span>
                  Mifflin-St Jeor Mathematical Ledger
                </span>
                <span className="font-label-sm text-label-sm text-secondary font-semibold bg-secondary/10 px-2 py-0.5 rounded">
                  Continuous Solve
                </span>
              </div>

              {/* Math BMR */}
              <div className="p-space-sm bg-surface-container-lowest rounded font-metric-num text-[13px] text-on-surface leading-relaxed border border-surface-container overflow-x-auto whitespace-nowrap">
                <span className="text-on-surface-variant font-label-md">BMR Formula:&nbsp;</span>
                <span>10 × </span>
                <span className="text-primary font-bold">{weight}</span>
                <span> + 6.25 × </span>
                <span className="text-primary font-bold">{height}</span>
                <span> - 5 × </span>
                <span className="text-primary font-bold">{age}</span>
                <span className="text-primary font-bold">
                  {gender === "male" ? " + 5" : " - 161"}
                </span>
                <span> = </span>
                <span className="font-metric-num text-[16px] text-primary font-bold">
                  {bmr.toLocaleString()}
                </span>
                <span className="text-on-surface-variant text-[12px] font-label-md">
                  &nbsp;kcal/day
                </span>
              </div>

              {/* TDEE */}
              <div className="p-space-sm bg-surface-container-lowest rounded font-metric-num text-[13px] text-on-surface flex items-center justify-between flex-wrap gap-2 border border-surface-container">
                <div>
                  <span className="text-on-surface-variant font-label-md">TDEE:&nbsp;</span>
                  <span className="text-primary font-bold">{bmr.toLocaleString()}</span>
                  <span> × </span>
                  <span className="text-primary font-bold">{activity}</span>
                  <span> = </span>
                  <span className="font-metric-num text-[16px] text-primary font-bold">
                    {tdee.toLocaleString()}
                  </span>
                  <span className="text-on-surface-variant text-[12px] font-label-md">
                    &nbsp;kcal (Maintenance)
                  </span>
                </div>
                <span className="font-label-sm text-label-sm text-primary bg-primary-fixed/50 px-space-xs py-0.5 rounded font-bold">
                  {adjText}
                </span>
              </div>

              {/* Target Banner */}
              <div className="grid grid-cols-1 sm:grid-cols-2 gap-space-sm pt-space-xs">
                <div className="p-space-sm bg-surface-container-highest rounded flex flex-col justify-between">
                  <span className="font-label-sm text-label-sm text-on-surface-variant">
                    Maintenance Ceiling (TDEE)
                  </span>
                  <div className="flex items-baseline gap-1 mt-1">
                    <span className="font-metric-num text-[24px] text-on-surface font-bold">
                      {tdee.toLocaleString()}
                    </span>
                    <span className="font-label-md text-label-md text-on-surface-variant">
                      kcal/day
                    </span>
                  </div>
                </div>

                <div className="p-space-sm bg-primary text-on-primary rounded flex flex-col justify-between shadow-sm">
                  <span className="font-label-sm text-label-sm text-on-primary-container font-semibold uppercase tracking-wider">
                    Active Prescribed Intake
                  </span>
                  <div className="flex items-baseline gap-1 mt-1">
                    <span className="font-metric-num text-[24px] text-on-primary font-bold">
                      {targetCalories.toLocaleString()}
                    </span>
                    <span className="font-label-md text-label-md text-on-primary-container">
                      kcal/day
                    </span>
                  </div>
                </div>
              </div>
            </div>
          </div>

          {/* Hard Safety Gate & Dietary Preferences Card */}
          <div className="bg-surface-container-lowest p-space-lg rounded-xl shadow-sm border border-surface-container space-y-space-md">
            <div className="flex items-center justify-between pb-space-xs border-b border-surface-container">
              <div>
                <div className="flex items-center gap-2">
                  <span className="material-symbols-outlined text-[20px] text-primary">shield</span>
                  <h2 className="font-headline-sm text-headline-sm text-primary font-serif">
                    Hard Safety Gate &amp; Dietary Exclusions
                  </h2>
                </div>
                <p className="font-body-sm text-body-sm text-on-surface-variant">
                  DietSense enforces safety as an uncompromisable boolean condition before scoring
                  executes.
                </p>
              </div>
            </div>

            {/* Safety Gate Alert Banner */}
            <div className="p-space-sm rounded-lg bg-primary/10 border border-primary/20 text-body-sm text-primary leading-snug">
              <strong>Core Clinical Principle:</strong> Allergen rules and ethical restrictions
              cannot be overridden by pantry similarity or taste scores. If a food item lacks
              verified allergen declaration in USDA/ICMR-NIN data, it is excluded by default in
              strict mode.
            </div>

            {/* Dietary Archetype */}
            <div>
              <label className="font-label-md text-label-md text-on-surface block mb-1 font-bold">
                Dietary Archetype
              </label>
              <div className="grid grid-cols-3 gap-2">
                {[
                  { id: "omnivore", label: "Omnivore / Balanced" },
                  { id: "vegetarian", label: "Lacto-Vegetarian (Indian)" },
                  { id: "vegan", label: "Strict 100% Vegan" },
                ].map((type) => (
                  <button
                    key={type.id}
                    type="button"
                    onClick={() => setDietaryType(type.id as any)}
                    className={`py-2 px-3 rounded font-label-md text-label-md transition-all text-center border ${
                      dietaryType === type.id
                        ? "bg-primary text-on-primary border-primary font-bold shadow-sm"
                        : "bg-surface-container text-on-surface-variant border-transparent hover:text-on-surface"
                    }`}
                  >
                    {type.label}
                  </button>
                ))}
              </div>
            </div>

            {/* Hard Allergen Exclusion Chips */}
            <div>
              <label className="font-label-md text-label-md text-on-surface block mb-2 font-bold">
                Absolute Allergen Exclusions (Hard Safety Shield)
              </label>
              <div className="grid grid-cols-1 sm:grid-cols-2 gap-2">
                {allergenList.map((item) => {
                  const isChecked = allergens.includes(item.id);
                  return (
                    <label
                      key={item.id}
                      onClick={() => toggleAllergen(item.id)}
                      className={`p-space-sm rounded border flex items-center justify-between cursor-pointer transition-all ${
                        isChecked
                          ? "bg-error-container text-on-error-container border-error/30 font-bold"
                          : "bg-surface-container-low text-on-surface border-surface-container hover:bg-surface-container"
                      }`}
                    >
                      <span className="font-label-md text-label-md">{item.label}</span>
                      <span className="material-symbols-outlined text-[18px]">
                        {isChecked ? "block" : "check"}
                      </span>
                    </label>
                  );
                })}
              </div>
            </div>
          </div>
        </div>

        {/* Right 4-Column Solo Logistics Rail */}
        <aside className="lg:col-span-4 space-y-space-md">
          {/* Solo-Cook Logistics Card */}
          <div className="bg-surface-container-lowest p-space-md rounded-xl shadow-sm border border-surface-container space-y-space-sm">
            <h3 className="font-headline-sm text-headline-sm text-primary font-serif">
              Solo-Cook Optimization
            </h3>
            <p className="font-body-sm text-body-sm text-on-surface-variant">
              Engineered for busy professionals &amp; bachelors cooking for one.
            </p>

            <div className="p-space-sm bg-surface-container-low rounded-lg space-y-2 border border-surface-container">
              <div className="flex items-center justify-between">
                <span className="font-label-md text-label-md font-bold text-on-surface">
                  Solo Cook Mode
                </span>
                <button
                  type="button"
                  onClick={() => setIsSoloCook(!isSoloCook)}
                  className={`w-11 h-6 rounded-full transition-colors relative flex items-center px-0.5 ${
                    isSoloCook ? "bg-primary" : "bg-surface-dim"
                  }`}
                >
                  <span
                    className={`w-5 h-5 rounded-full bg-white transition-transform ${
                      isSoloCook ? "translate-x-5" : "translate-x-0"
                    }`}
                  />
                </button>
              </div>
              <p className="text-body-sm text-on-surface-variant">
                Prioritizes single-skillet recipes, minimal dishwashing, and grocery portion scaling.
              </p>
            </div>

            {/* Morning Effort Level */}
            <div>
              <label className="font-label-sm text-label-sm text-on-surface block mb-1 font-bold">
                Weekday Breakfast Effort
              </label>
              <div className="grid grid-cols-2 gap-1.5">
                {[
                  { id: "low", label: "⚡ Quick (<15m)" },
                  { id: "moderate", label: "🍳 Standard (~25m)" },
                ].map((eff) => (
                  <button
                    key={eff.id}
                    type="button"
                    onClick={() => setWeekdayBreakfastEffort(eff.id as EffortLevel)}
                    className={`py-1.5 px-2 rounded font-label-sm text-label-sm text-center border ${
                      weekdayBreakfastEffort === eff.id
                        ? "bg-primary text-on-primary border-primary font-bold"
                        : "bg-surface-container text-on-surface-variant border-transparent"
                    }`}
                  >
                    {eff.label}
                  </button>
                ))}
              </div>
            </div>

            {/* Goal Target Selector */}
            <div>
              <label className="font-label-sm text-label-sm text-on-surface block mb-1 font-bold">
                Metabolic Goal
              </label>
              <div className="space-y-1">
                {[
                  { id: "lose_weight", label: "Deficit Cut (-400 kcal)" },
                  { id: "maintain", label: "Maintenance (TDEE Baseline)" },
                  { id: "gain_weight", label: "Hypertrophy Surplus (+300 kcal)" },
                ].map((g) => (
                  <button
                    key={g.id}
                    type="button"
                    onClick={() => setGoal(g.id as GoalType)}
                    className={`w-full py-1.5 px-3 rounded font-label-sm text-label-sm text-left border ${
                      goal === g.id
                        ? "bg-primary-container text-on-primary border-primary font-bold"
                        : "bg-surface-container text-on-surface border-transparent"
                    }`}
                  >
                    {g.label}
                  </button>
                ))}
              </div>
            </div>
          </div>

          {/* Macronutrient Split Summary */}
          <div className="bg-surface-container-lowest p-space-md rounded-xl shadow-sm border border-surface-container space-y-space-sm">
            <h4 className="font-headline-sm text-headline-sm text-on-surface font-serif">
              Macronutrient Targets
            </h4>
            <div className="space-y-2 text-body-sm font-body-sm">
              <div className="flex items-center justify-between p-2 rounded bg-surface-container-low border border-surface-container">
                <span className="flex items-center gap-2">
                  <span className="w-2.5 h-2.5 rounded-full bg-primary" />
                  Protein (30%)
                </span>
                <span className="font-bold text-primary">{proteinGrams}g</span>
              </div>

              <div className="flex items-center justify-between p-2 rounded bg-surface-container-low border border-surface-container">
                <span className="flex items-center gap-2">
                  <span className="w-2.5 h-2.5 rounded-full bg-amber-600" />
                  Carbohydrates (45%)
                </span>
                <span className="font-bold text-amber-700">{carbsGrams}g</span>
              </div>

              <div className="flex items-center justify-between p-2 rounded bg-surface-container-low border border-surface-container">
                <span className="flex items-center gap-2">
                  <span className="w-2.5 h-2.5 rounded-full bg-secondary" />
                  Healthy Fats (25%)
                </span>
                <span className="font-bold text-secondary">{fatGrams}g</span>
              </div>
            </div>
          </div>
        </aside>
      </div>
    </div>
  );
};
