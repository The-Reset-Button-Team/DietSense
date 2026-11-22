"use client";

import React, { useState, useEffect } from "react";
import { BudgetType, BudgetFilteringMode } from "@/types";

interface BudgetFilterProps {
  budgetAmount: number | null;
  budgetType: BudgetType;
  budgetMode: BudgetFilteringMode;
  onBudgetChange: (amount: number | null) => void;
  onBudgetTypeChange: (type: BudgetType) => void;
  onBudgetModeChange: (mode: BudgetFilteringMode) => void;
  onClearBudget: () => void;
  isLoading?: boolean;
}

const QUICK_AMOUNTS = [50, 100, 150, 200, 300, 500];

export const BudgetFilter: React.FC<BudgetFilterProps> = ({
  budgetAmount,
  budgetType,
  budgetMode,
  onBudgetChange,
  onBudgetTypeChange,
  onBudgetModeChange,
  onClearBudget,
  isLoading = false,
}) => {
  const [manualInput, setManualInput] = useState<string>(
    budgetAmount !== null ? String(budgetAmount) : ""
  );
  const [validationError, setValidationError] = useState<string | null>(null);

  // Sync manual input when external budgetAmount changes
  useEffect(() => {
    if (budgetAmount !== null) {
      setManualInput(String(budgetAmount));
    } else {
      setManualInput("");
    }
    setValidationError(null);
  }, [budgetAmount]);

  const handleQuickSelect = (amt: number) => {
    setValidationError(null);
    if (budgetAmount === amt) {
      // Clicking same quick amount toggles or keeps it
      onBudgetChange(amt);
    } else {
      onBudgetChange(amt);
    }
  };

  const handleApplyManual = (e?: React.FormEvent) => {
    if (e) e.preventDefault();
    setValidationError(null);

    const trimmed = manualInput.trim();
    if (!trimmed) {
      setValidationError("Please enter a budget amount in ₹.");
      return;
    }

    const parsed = Number(trimmed);
    if (isNaN(parsed)) {
      setValidationError("Please enter a valid numeric amount.");
      return;
    }

    if (parsed <= 0) {
      setValidationError("Budget must be greater than ₹0.");
      return;
    }

    onBudgetChange(Math.round(parsed * 100) / 100);
  };

  const handleClear = () => {
    setManualInput("");
    setValidationError(null);
    onClearBudget();
  };

  const isQuickActive = (amt: number) => budgetAmount === amt;

  return (
    <section
      aria-label="Budget-Aware Meal Recommendation Filter"
      className="bg-surface-container-lowest p-space-md md:p-space-lg rounded-xl shadow-sm border border-surface-container space-y-space-md"
    >
      {/* Header & Active Status Indicator */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-space-xs pb-space-xs border-b border-surface-container">
        <div className="flex items-center gap-space-xs flex-wrap">
          <div className="w-8 h-8 rounded-full bg-secondary/15 flex items-center justify-center text-secondary">
            <span className="material-symbols-outlined text-[18px]">currency_rupee</span>
          </div>
          <div>
            <h2 className="font-headline-sm text-headline-sm text-primary font-serif flex items-center gap-2">
              Budget &amp; Affordability Filter
            </h2>
            <p className="font-body-sm text-body-sm text-on-surface-variant">
              Discover meals aligned with your clinical targets within your preferred budget.
            </p>
          </div>
        </div>

        {/* Current Active Indicator Pill */}
        <div className="flex items-center gap-2">
          {budgetAmount !== null ? (
            <div className="px-3 py-1 rounded-full bg-secondary/10 border border-secondary/20 flex items-center gap-1.5 text-secondary font-label-sm text-label-sm font-bold">
              <span className="material-symbols-outlined text-[15px]">check_circle</span>
              <span>
                Active: ₹{budgetAmount} / {budgetType === "per_meal" ? "meal" : "day"} (
                {budgetMode === "within_budget"
                  ? "Within Budget"
                  : budgetMode === "slightly_above"
                  ? "Slightly Above"
                  : "Show All"}
                )
              </span>
            </div>
          ) : (
            <div className="px-3 py-1 rounded-full bg-surface-container text-on-surface-variant font-label-sm text-label-sm font-semibold flex items-center gap-1.5">
              <span className="material-symbols-outlined text-[15px]">tune</span>
              <span>No Budget Limit (Unrestricted)</span>
            </div>
          )}

          {budgetAmount !== null && (
            <button
              type="button"
              onClick={handleClear}
              className="px-2.5 py-1 text-on-surface-variant hover:text-error hover:bg-surface-container rounded font-label-sm text-label-sm transition-colors flex items-center gap-1"
              title="Clear budget filter and restore unrestricted recommendations"
            >
              <span className="material-symbols-outlined text-[14px]">close</span>
              <span>Clear Filter</span>
            </button>
          )}
        </div>
      </div>

      {/* Row 1: Budget Type Toggle & Quick Selection Buttons */}
      <div className="grid grid-cols-1 lg:grid-cols-12 gap-space-md items-center">
        {/* Budget Type Segmented Control */}
        <div className="lg:col-span-4 space-y-1">
          <label className="font-label-sm text-label-sm uppercase tracking-wider text-on-surface-variant font-bold block">
            Budget Type
          </label>
          <div className="grid grid-cols-2 gap-1 bg-surface-container p-1 rounded-lg">
            <button
              type="button"
              onClick={() => onBudgetTypeChange("per_meal")}
              className={`py-1.5 px-3 rounded font-label-md text-label-md transition-all text-center flex items-center justify-center gap-1.5 ${
                budgetType === "per_meal"
                  ? "bg-primary text-on-primary font-bold shadow-sm"
                  : "text-on-surface-variant hover:text-on-surface hover:bg-surface-container-high"
              }`}
            >
              <span className="material-symbols-outlined text-[16px]">restaurant</span>
              <span>Per Meal</span>
            </button>
            <button
              type="button"
              onClick={() => onBudgetTypeChange("per_day")}
              className={`py-1.5 px-3 rounded font-label-md text-label-md transition-all text-center flex items-center justify-center gap-1.5 ${
                budgetType === "per_day"
                  ? "bg-primary text-on-primary font-bold shadow-sm"
                  : "text-on-surface-variant hover:text-on-surface hover:bg-surface-container-high"
              }`}
            >
              <span className="material-symbols-outlined text-[16px]">calendar_today</span>
              <span>Per Day</span>
            </button>
          </div>
        </div>

        {/* Quick Budget Buttons */}
        <div className="lg:col-span-8 space-y-1">
          <label className="font-label-sm text-label-sm uppercase tracking-wider text-on-surface-variant font-bold block">
            Quick Budget Presets ({budgetType === "per_meal" ? "Per Meal" : "Per Day"})
          </label>
          <div className="flex flex-wrap items-center gap-1.5">
            {QUICK_AMOUNTS.map((amt) => {
              const active = isQuickActive(amt);
              return (
                <button
                  key={amt}
                  type="button"
                  onClick={() => handleQuickSelect(amt)}
                  className={`px-3.5 py-1.5 rounded-lg font-label-md text-label-md transition-all flex items-center gap-1 border ${
                    active
                      ? "bg-secondary text-white border-secondary font-bold shadow-sm ring-2 ring-secondary/20"
                      : "bg-surface-container-low hover:bg-surface-container text-on-surface border-surface-container"
                  }`}
                >
                  <span className="text-[13px] font-sans">₹</span>
                  <span>{amt}</span>
                </button>
              );
            })}
          </div>
        </div>
      </div>

      {/* Row 2: Manual Budget Entry & Filtering Mode Selection */}
      <div className="grid grid-cols-1 lg:grid-cols-12 gap-space-md items-start pt-space-xs border-t border-surface-container">
        {/* Manual Input Form */}
        <div className="lg:col-span-5 space-y-1">
          <label
            htmlFor="manual-budget-input"
            className="font-label-sm text-label-sm uppercase tracking-wider text-on-surface-variant font-bold block"
          >
            Custom Budget Entry
          </label>
          <form onSubmit={handleApplyManual} className="flex items-center gap-1.5">
            <div className="relative flex-1">
              <span className="absolute left-3 top-1/2 -translate-y-1/2 text-on-surface-variant font-bold font-sans text-sm">
                ₹
              </span>
              <input
                id="manual-budget-input"
                type="number"
                min="1"
                step="any"
                placeholder="Enter your budget (₹)"
                value={manualInput}
                onChange={(e) => {
                  setManualInput(e.target.value);
                  setValidationError(null);
                }}
                className="w-full pl-8 pr-3 py-2 bg-surface-container-low border border-surface-container rounded-lg font-body-sm text-body-sm text-on-surface placeholder:text-on-surface-variant/60 focus:outline-none focus:ring-2 focus:ring-primary/30 focus:border-primary transition-all"
              />
            </div>
            <button
              type="submit"
              disabled={isLoading}
              className="px-4 py-2 bg-primary hover:bg-primary-container text-on-primary rounded-lg font-label-md text-label-md font-bold transition-all shadow-sm shrink-0 disabled:opacity-50"
            >
              Apply
            </button>
          </form>
          {validationError && (
            <p className="font-body-sm text-body-sm text-error font-medium flex items-center gap-1 pt-0.5">
              <span className="material-symbols-outlined text-[14px]">error</span>
              <span>{validationError}</span>
            </p>
          )}
        </div>

        {/* Filtering Modes */}
        <div className="lg:col-span-7 space-y-1">
          <label className="font-label-sm text-label-sm uppercase tracking-wider text-on-surface-variant font-bold block">
            Filtering Mode
          </label>
          <div className="grid grid-cols-3 gap-1.5 bg-surface-container p-1 rounded-lg">
            <button
              type="button"
              onClick={() => onBudgetModeChange("within_budget")}
              className={`py-1.5 px-2 rounded font-label-md text-label-md transition-all text-center flex flex-col sm:flex-row items-center justify-center gap-1 ${
                budgetMode === "within_budget"
                  ? "bg-secondary text-white font-bold shadow-sm"
                  : "text-on-surface-variant hover:text-on-surface hover:bg-surface-container-high"
              }`}
            >
              <span className="material-symbols-outlined text-[15px]">verified</span>
              <span>Within Budget</span>
            </button>
            <button
              type="button"
              onClick={() => onBudgetModeChange("slightly_above")}
              className={`py-1.5 px-2 rounded font-label-md text-label-md transition-all text-center flex flex-col sm:flex-row items-center justify-center gap-1 ${
                budgetMode === "slightly_above"
                  ? "bg-amber-600 text-white font-bold shadow-sm"
                  : "text-on-surface-variant hover:text-on-surface hover:bg-surface-container-high"
              }`}
            >
              <span className="material-symbols-outlined text-[15px]">trending_up</span>
              <span>Slightly Above</span>
            </button>
            <button
              type="button"
              onClick={() => onBudgetModeChange("show_all")}
              className={`py-1.5 px-2 rounded font-label-md text-label-md transition-all text-center flex flex-col sm:flex-row items-center justify-center gap-1 ${
                budgetMode === "show_all"
                  ? "bg-primary text-on-primary font-bold shadow-sm"
                  : "text-on-surface-variant hover:text-on-surface hover:bg-surface-container-high"
              }`}
            >
              <span className="material-symbols-outlined text-[15px]">visibility</span>
              <span>Show All</span>
            </button>
          </div>
          <p className="font-body-sm text-body-sm text-on-surface-variant text-[11px] px-1">
            {budgetMode === "within_budget" &&
              "Only displays meals strictly at or below your selected budget with verified/estimated pricing."}
            {budgetMode === "slightly_above" &&
              "Displays meals within budget plus options slightly above (+20% tolerance), showing the price difference."}
            {budgetMode === "show_all" &&
              "Displays all clinically suitable meals regardless of price, with costs clearly marked."}
          </p>
        </div>
      </div>
    </section>
  );
};
