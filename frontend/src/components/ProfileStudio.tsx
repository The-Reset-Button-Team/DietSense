"use client";

import React, { useState, useEffect } from "react";
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

export type DietaryType = "vegetarian" | "vegan" | "eggetarian" | "pescatarian" | "omnivore";

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
  const { user, updateProfile, changePassword, logout } = useAuth();

  // Dietary and allergen state
  const [dietaryType, setDietaryType] = useState<DietaryType>(
    (user?.dietary_preference || user?.dietary_pref || "vegetarian") as DietaryType
  );
  const [allergens, setAllergens] = useState<string[]>(
    user?.allergies || ["peanuts"]
  );

  // Budget & Prep Time preferences
  const [budgetPerMeal, setBudgetPerMeal] = useState<number>(
    user?.budget_per_meal !== undefined ? Number(user?.budget_per_meal) : 100
  );
  const [prepTimeLimit, setPrepTimeLimit] = useState<number>(
    user?.prep_time_limit !== undefined ? Number(user?.prep_time_limit) : 30
  );

  // Account management state
  const [fullName, setFullName] = useState<string>(user?.full_name || "");
  const [currentPassword, setCurrentPassword] = useState("");
  const [newPassword, setNewPassword] = useState("");
  const [confirmPassword, setConfirmPassword] = useState("");
  const [passwordStatusMsg, setPasswordStatusMsg] = useState<string | null>(null);
  const [passwordErrorMsg, setPasswordErrorMsg] = useState<string | null>(null);
  const [isChangingPassword, setIsChangingPassword] = useState(false);

  const [isSaved, setIsSaved] = useState(false);
  const [saveError, setSaveError] = useState<string | null>(null);

  // Sync state if auth user updates
  useEffect(() => {
    if (user) {
      if (user.dietary_preference || user.dietary_pref) {
        setDietaryType((user.dietary_preference || user.dietary_pref) as DietaryType);
      }
      if (user.allergies) {
        setAllergens(user.allergies);
      }
      if (user.budget_per_meal !== undefined) {
        setBudgetPerMeal(Number(user.budget_per_meal));
      }
      if (user.prep_time_limit !== undefined) {
        setPrepTimeLimit(Number(user.prep_time_limit));
      }
      if (user.full_name) {
        setFullName(user.full_name);
      }
    }
  }, [user]);

  const toggleAllergen = (id: string) => {
    if (allergens.includes(id)) {
      setAllergens(allergens.filter((a) => a !== id));
    } else {
      setAllergens([...allergens, id]);
    }
  };

  const handleSave = async () => {
    try {
      setSaveError(null);
      if (updateProfile) {
        await updateProfile({
          full_name: fullName.trim() || user?.full_name || "User",
          age,
          gender,
          weight_kg: weight,
          height_cm: height,
          goal,
          dietary_pref: dietaryType,
          dietary_preference: dietaryType,
          allergies: allergens,
          budget_per_meal: budgetPerMeal,
          prep_time_limit: prepTimeLimit,
          is_solo_cook: isSoloCook,
          active_meal_frequency: mealFrequency,
        });
      }
      setIsSaved(true);
      setTimeout(() => setIsSaved(false), 3500);
    } catch (err: any) {
      setSaveError(err?.message || "Failed to save profile changes.");
      setTimeout(() => setSaveError(null), 4000);
    }
  };

  const handleChangePassword = async (e: React.FormEvent) => {
    e.preventDefault();
    setPasswordErrorMsg(null);
    setPasswordStatusMsg(null);

    if (newPassword.length < 6) {
      setPasswordErrorMsg("New password must be at least 6 characters.");
      return;
    }
    if (newPassword !== confirmPassword) {
      setPasswordErrorMsg("New passwords do not match.");
      return;
    }

    setIsChangingPassword(true);
    try {
      const res = await changePassword(currentPassword, newPassword);
      if (res.success) {
        setPasswordStatusMsg("Password updated successfully.");
        setCurrentPassword("");
        setNewPassword("");
        setConfirmPassword("");
        setTimeout(() => setPasswordStatusMsg(null), 4000);
      } else {
        setPasswordErrorMsg(res.error || "Failed to change password.");
      }
    } catch (err: any) {
      setPasswordErrorMsg(err?.message || "An error occurred while changing password.");
    } finally {
      setIsChangingPassword(false);
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
    { id: "tree_nuts", label: "Tree Nuts (Walnuts, Cashews, Almonds)" },
    { id: "dairy", label: "Lactose / Dairy" },
    { id: "gluten", label: "Gluten & Wheat" },
    { id: "eggs", label: "Eggs" },
    { id: "fish", label: "Fish" },
    { id: "shellfish", label: "Shellfish & Crustaceans" },
    { id: "soy", label: "Soy & Edamame" },
  ];

  const dietaryOptions: { id: DietaryType; label: string; desc: string }[] = [
    { id: "vegetarian", label: "Lacto-Vegetarian", desc: "Plant foods + dairy, no meat, fish or eggs" },
    { id: "eggetarian", label: "Ovo-Vegetarian / Eggetarian", desc: "Plant foods + dairy + eggs, no meat or fish" },
    { id: "vegan", label: "Strict 100% Vegan", desc: "Exclusively plant foods, 0 animal byproducts" },
    { id: "pescatarian", label: "Pescatarian", desc: "Vegetarian + fish & seafood" },
    { id: "omnivore", label: "Omnivore / Balanced", desc: "All food groups including poultry & meat" },
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
            Profile Studio &amp; Settings
          </h1>
          <p className="font-body-md text-body-md text-on-surface-variant max-w-2xl">
            Configure your biometrics, dietary restrictions, financial ceiling, and preparation limits.
            These settings directly constrain and steer the recommendation engine.
          </p>
        </div>

        <button
          type="button"
          onClick={handleSave}
          className="px-space-lg py-2.5 bg-primary hover:bg-primary-container text-on-primary rounded font-label-md text-label-md transition-all shadow-sm flex items-center gap-2 self-start lg:self-auto"
        >
          <span className="material-symbols-outlined text-[18px]">save</span>
          Save Profile Changes
        </button>
      </div>

      {isSaved && (
        <div className="p-space-sm rounded-lg bg-secondary/10 border border-secondary text-secondary font-label-md flex items-center gap-2 animate-in fade-in">
          <span className="material-symbols-outlined text-[18px]">check_circle</span>
          Profile settings and dietary constraints synchronized with local SQLite.
        </div>
      )}

      {saveError && (
        <div className="p-space-sm rounded-lg bg-error-container text-on-error-container border border-error/30 font-label-md flex items-center gap-2 animate-in fade-in">
          <span className="material-symbols-outlined text-[18px]">error</span>
          {saveError}
        </div>
      )}

      {/* Grid: 8-Column Engine + 4-Column Logistics Rail */}
      <div className="grid grid-cols-1 lg:grid-cols-12 gap-space-lg items-start">
        {/* Left 8-Column Main Studio */}
        <div className="lg:col-span-8 space-y-space-lg">
          {/* 1. Dietary Archetype & Hard Safety Gate */}
          <div className="bg-surface-container-lowest p-space-lg rounded-xl shadow-sm border border-surface-container space-y-space-md">
            <div className="flex items-center justify-between pb-space-xs border-b border-surface-container">
              <div>
                <div className="flex items-center gap-2">
                  <span className="material-symbols-outlined text-[20px] text-primary">shield</span>
                  <h2 className="font-headline-sm text-headline-sm text-primary font-serif">
                    Dietary Preference &amp; Hard Safety Gate
                  </h2>
                </div>
                <p className="font-body-sm text-body-sm text-on-surface-variant">
                  Absolute boolean filters applied before scoring. Excluded foods will never appear in recommendations.
                </p>
              </div>
            </div>

            {/* Safety Principle Banner */}
            <div className="p-space-sm rounded-lg bg-primary/10 border border-primary/20 text-body-sm text-primary leading-snug">
              <strong>Core Clinical Principle:</strong> Allergen rules and ethical restrictions cannot be overridden by taste scores or pantry bonuses.
            </div>

            {/* Dietary Preference Selectors */}
            <div>
              <label className="font-label-md text-label-md text-on-surface block mb-2 font-bold">
                Dietary Preference Archetype
              </label>
              <div className="grid grid-cols-1 sm:grid-cols-2 md:grid-cols-3 gap-2">
                {dietaryOptions.map((type) => {
                  const isSelected = dietaryType === type.id;
                  return (
                    <button
                      key={type.id}
                      type="button"
                      onClick={() => setDietaryType(type.id)}
                      className={`p-space-sm rounded text-left transition-all border ${
                        isSelected
                          ? "bg-primary text-on-primary border-primary font-bold shadow-sm"
                          : "bg-surface-container text-on-surface-variant border-transparent hover:text-on-surface hover:bg-surface-container-high"
                      }`}
                    >
                      <div className="font-label-md text-label-md font-semibold">{type.label}</div>
                      <div className={`font-body-sm text-[11px] mt-0.5 ${isSelected ? "text-primary-fixed" : "text-on-surface-variant"}`}>
                        {type.desc}
                      </div>
                    </button>
                  );
                })}
              </div>
            </div>

            {/* Allergen Exclusions */}
            <div>
              <label className="font-label-md text-label-md text-on-surface block mb-2 font-bold">
                Declared Allergens (Strict Boolean Exclusion)
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

          {/* 2. Budget & Preparation Time Preferences */}
          <div className="bg-surface-container-lowest p-space-lg rounded-xl shadow-sm border border-surface-container space-y-space-md">
            <div className="flex items-center justify-between pb-space-xs border-b border-surface-container">
              <div>
                <div className="flex items-center gap-2">
                  <span className="material-symbols-outlined text-[20px] text-primary">payments</span>
                  <h2 className="font-headline-sm text-headline-sm text-primary font-serif">
                    Budget &amp; Preparation Constraints
                  </h2>
                </div>
                <p className="font-body-sm text-body-sm text-on-surface-variant">
                  Set economic and cooking time targets for meal scoring calculations.
                </p>
              </div>
            </div>

            <div className="grid grid-cols-1 sm:grid-cols-2 gap-space-md">
              {/* Budget Per Meal */}
              <div className="space-y-2 p-space-sm bg-surface-container-low rounded-lg border border-surface-container">
                <div className="flex justify-between items-center">
                  <label className="font-label-md text-label-md font-bold text-on-surface flex items-center gap-1">
                    <span className="material-symbols-outlined text-[16px] text-primary">currency_rupee</span>
                    Budget Per Meal
                  </label>
                  <span className="font-metric-num text-[18px] text-primary font-bold">
                    ₹{budgetPerMeal}
                  </span>
                </div>
                <input
                  type="range"
                  min="40"
                  max="400"
                  step="10"
                  value={budgetPerMeal}
                  onChange={(e) => setBudgetPerMeal(Number(e.target.value))}
                  className="w-full h-2 bg-surface-variant rounded-lg appearance-none cursor-pointer accent-primary"
                />
                <div className="flex justify-between text-body-sm text-[11px] text-on-surface-variant">
                  <span>₹40 (Frugal)</span>
                  <span>₹100 (Standard)</span>
                  <span>₹400 (Premium)</span>
                </div>
                <div className="flex gap-1 pt-1">
                  {[60, 100, 150, 250].map((preset) => (
                    <button
                      key={preset}
                      type="button"
                      onClick={() => setBudgetPerMeal(preset)}
                      className={`px-2 py-1 text-[11px] rounded font-label-sm ${
                        budgetPerMeal === preset
                          ? "bg-primary text-on-primary font-bold"
                          : "bg-surface-container text-on-surface-variant hover:text-on-surface"
                      }`}
                    >
                      ₹{preset}
                    </button>
                  ))}
                </div>
              </div>

              {/* Prep Time Limit */}
              <div className="space-y-2 p-space-sm bg-surface-container-low rounded-lg border border-surface-container">
                <div className="flex justify-between items-center">
                  <label className="font-label-md text-label-md font-bold text-on-surface flex items-center gap-1">
                    <span className="material-symbols-outlined text-[16px] text-primary">timer</span>
                    Preparation Time Limit
                  </label>
                  <span className="font-metric-num text-[18px] text-primary font-bold">
                    {prepTimeLimit} mins
                  </span>
                </div>
                <input
                  type="range"
                  min="10"
                  max="90"
                  step="5"
                  value={prepTimeLimit}
                  onChange={(e) => setPrepTimeLimit(Number(e.target.value))}
                  className="w-full h-2 bg-surface-variant rounded-lg appearance-none cursor-pointer accent-primary"
                />
                <div className="flex justify-between text-body-sm text-[11px] text-on-surface-variant">
                  <span>10 min (Quick)</span>
                  <span>30 min (Default)</span>
                  <span>90 min (Elaborate)</span>
                </div>
                <div className="flex gap-1 pt-1">
                  {[15, 25, 30, 45, 60].map((preset) => (
                    <button
                      key={preset}
                      type="button"
                      onClick={() => setPrepTimeLimit(preset)}
                      className={`px-2 py-1 text-[11px] rounded font-label-sm ${
                        prepTimeLimit === preset
                          ? "bg-primary text-on-primary font-bold"
                          : "bg-surface-container text-on-surface-variant hover:text-on-surface"
                      }`}
                    >
                      {preset}m
                    </button>
                  ))}
                </div>
              </div>
            </div>
          </div>

          {/* 3. Mifflin-St Jeor Biometric Engine Card */}
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

          {/* 4. Account Management & Security Card */}
          <div className="bg-surface-container-lowest p-space-lg rounded-xl shadow-sm border border-surface-container space-y-space-md">
            <div className="flex items-center justify-between pb-space-xs border-b border-surface-container">
              <div>
                <div className="flex items-center gap-2">
                  <span className="material-symbols-outlined text-[20px] text-primary">manage_accounts</span>
                  <h2 className="font-headline-sm text-headline-sm text-primary font-serif">
                    Account &amp; Security Management
                  </h2>
                </div>
                <p className="font-body-sm text-body-sm text-on-surface-variant">
                  Manage your authenticated credentials, display name, and local data isolation.
                </p>
              </div>
            </div>

            {/* User Identity Details */}
            <div className="grid grid-cols-1 sm:grid-cols-2 gap-space-sm">
              <div>
                <label className="font-label-sm text-label-sm text-on-surface-variant block mb-1">
                  Full Name / Alias
                </label>
                <input
                  type="text"
                  value={fullName}
                  onChange={(e) => setFullName(e.target.value)}
                  placeholder="Your Name"
                  className="w-full px-3 py-2 rounded bg-surface-container border border-surface-container text-body-md text-on-surface focus:outline-none focus:ring-1 focus:ring-primary"
                />
              </div>

              <div>
                <label className="font-label-sm text-label-sm text-on-surface-variant block mb-1">
                  Account Email
                </label>
                <input
                  type="email"
                  value={user?.email || "offline@dietsense.local"}
                  disabled
                  className="w-full px-3 py-2 rounded bg-surface-container-high/50 border border-surface-container text-body-md text-on-surface-variant cursor-not-allowed"
                />
              </div>
            </div>

            {/* Provider and Data Isolation Status */}
            <div className="flex flex-wrap items-center justify-between gap-2 p-space-sm bg-surface-container-low rounded-lg border border-surface-container text-body-sm">
              <div className="flex items-center gap-2">
                <span className="material-symbols-outlined text-[18px] text-secondary">database</span>
                <span>
                  User ID: <code className="font-mono text-[12px] bg-surface-container px-1 py-0.5 rounded">{user?.id || "local_user"}</code>
                </span>
              </div>
              <div className="flex items-center gap-2">
                <span className="px-2 py-0.5 rounded-full text-[11px] font-label-sm bg-secondary/10 text-secondary font-bold">
                  {(user?.auth_providers || ["local"]).join(", ")} auth
                </span>
                <span className="px-2 py-0.5 rounded-full text-[11px] font-label-sm bg-primary/10 text-primary font-bold">
                  Isolated SQLite Storage
                </span>
              </div>
            </div>

            {/* Change Password Sub-form */}
            <form onSubmit={handleChangePassword} className="space-y-space-xs pt-space-xs border-t border-surface-container">
              <h4 className="font-label-md text-label-md font-bold text-on-surface flex items-center gap-1">
                <span className="material-symbols-outlined text-[16px]">lock_reset</span>
                Change Account Password
              </h4>

              {passwordStatusMsg && (
                <div className="p-2 rounded bg-secondary/10 text-secondary text-body-sm border border-secondary flex items-center gap-2">
                  <span className="material-symbols-outlined text-[16px]">check_circle</span>
                  {passwordStatusMsg}
                </div>
              )}

              {passwordErrorMsg && (
                <div className="p-2 rounded bg-error-container text-on-error-container text-body-sm border border-error/30 flex items-center gap-2">
                  <span className="material-symbols-outlined text-[16px]">error</span>
                  {passwordErrorMsg}
                </div>
              )}

              <div className="grid grid-cols-1 sm:grid-cols-3 gap-2">
                <input
                  type="password"
                  value={currentPassword}
                  onChange={(e) => setCurrentPassword(e.target.value)}
                  placeholder="Current Password"
                  className="px-3 py-2 rounded bg-surface-container border border-surface-container text-body-sm text-on-surface focus:outline-none focus:ring-1 focus:ring-primary"
                />
                <input
                  type="password"
                  value={newPassword}
                  onChange={(e) => setNewPassword(e.target.value)}
                  placeholder="New Password (min 6)"
                  className="px-3 py-2 rounded bg-surface-container border border-surface-container text-body-sm text-on-surface focus:outline-none focus:ring-1 focus:ring-primary"
                />
                <input
                  type="password"
                  value={confirmPassword}
                  onChange={(e) => setConfirmPassword(e.target.value)}
                  placeholder="Confirm New Password"
                  className="px-3 py-2 rounded bg-surface-container border border-surface-container text-body-sm text-on-surface focus:outline-none focus:ring-1 focus:ring-primary"
                />
              </div>

              <div className="flex justify-between items-center pt-2">
                <button
                  type="button"
                  onClick={() => logout()}
                  className="px-3 py-1.5 text-error hover:bg-error-container/20 rounded font-label-sm text-label-sm flex items-center gap-1 transition-colors"
                >
                  <span className="material-symbols-outlined text-[16px]">logout</span>
                  Sign Out
                </button>

                <button
                  type="submit"
                  disabled={isChangingPassword || !newPassword}
                  className="px-4 py-1.5 bg-primary hover:bg-primary-container text-on-primary rounded font-label-sm text-label-sm disabled:opacity-50 transition-all shadow-sm"
                >
                  {isChangingPassword ? "Updating..." : "Update Password"}
                </button>
              </div>
            </form>
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
