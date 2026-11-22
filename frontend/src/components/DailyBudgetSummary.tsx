"use client";

import React from "react";
import { DailyBudgetSummary as DailyBudgetSummaryType, BudgetType } from "@/types";

interface DailyBudgetSummaryProps {
  summary: DailyBudgetSummaryType | null;
  budgetType: BudgetType;
  budgetAmount: number | null;
}

export const DailyBudgetSummary: React.FC<DailyBudgetSummaryProps> = ({
  summary,
  budgetType,
  budgetAmount,
}) => {
  if (!summary) return null;

  const slotLabels: Record<string, string> = {
    early_morning: "Early Morning",
    breakfast: "Breakfast",
    lunch: "Lunch",
    evening_snack: "Evening Snack",
    dinner: "Dinner",
  };

  const activeSlots = Object.keys(summary.slot_costs || {});
  const isPerDay = budgetType === "per_day" && budgetAmount !== null && budgetAmount > 0;
  const isPerMeal = budgetType === "per_meal" && budgetAmount !== null && budgetAmount > 0;

  return (
    <div
      aria-label="Daily Meal Plan Budget Summary"
      className="bg-surface-container-low p-space-md rounded-xl border border-surface-container space-y-space-sm"
    >
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-space-xs pb-space-xs border-b border-surface-container">
        <div className="flex items-center gap-2">
          <span className="material-symbols-outlined text-[20px] text-primary">receipt_long</span>
          <h3 className="font-headline-sm text-sm text-primary font-serif font-bold">
            Daily Meal Plan Budget Breakdown
          </h3>
          {summary.is_complete ? (
            <span className="px-2 py-0.5 rounded-full bg-secondary/15 text-secondary font-label-sm text-[11px] font-bold flex items-center gap-1">
              <span className="material-symbols-outlined text-[12px]">check</span>
              Complete Pricing
            </span>
          ) : (
            <span className="px-2 py-0.5 rounded-full bg-amber-500/15 text-amber-700 font-label-sm text-[11px] font-bold flex items-center gap-1">
              <span className="material-symbols-outlined text-[12px]">warning</span>
              Incomplete Pricing
            </span>
          )}
        </div>

        {/* Header Metric */}
        {isPerDay && (
          <div className="flex items-center gap-2 text-on-surface">
            <span className="font-label-sm text-label-sm text-on-surface-variant">Daily Budget:</span>
            <span className="font-metric-num text-sm text-primary font-bold">₹{budgetAmount}</span>
          </div>
        )}
        {isPerMeal && (
          <div className="flex items-center gap-2 text-on-surface">
            <span className="font-label-sm text-label-sm text-on-surface-variant">Target per meal:</span>
            <span className="font-metric-num text-sm text-primary font-bold">₹{budgetAmount}</span>
          </div>
        )}
      </div>

      {/* Grid of Slots & Costs */}
      <div className="grid grid-cols-2 sm:grid-cols-3 lg:grid-cols-5 gap-2">
        {activeSlots.map((slotKey) => {
          const cost = summary.slot_costs[slotKey];
          const alloc = summary.slot_budget_allocations?.[slotKey];
          const label = slotLabels[slotKey] || slotKey;

          return (
            <div
              key={slotKey}
              className="bg-surface-container-lowest p-2.5 rounded-lg border border-surface-container space-y-1"
            >
              <div className="font-label-sm text-[11px] text-on-surface-variant font-bold truncate">
                {label}
              </div>
              <div className="font-metric-num text-sm text-primary font-bold">
                {cost !== null && cost !== undefined ? `₹${cost.toFixed(2)}` : "Price unavailable"}
              </div>
              {isPerDay && alloc !== undefined && alloc !== null && (
                <div className="font-body-sm text-[10px] text-on-surface-variant">
                  Target: ₹{alloc.toFixed(2)}
                </div>
              )}
              {isPerMeal && cost !== null && cost !== undefined && (
                <div className="font-body-sm text-[10px]">
                  {cost <= (budgetAmount || 0) ? (
                    <span className="text-secondary font-semibold">Within ₹{budgetAmount}</span>
                  ) : (
                    <span className="text-amber-700 font-semibold">
                      +₹{(cost - (budgetAmount || 0)).toFixed(2)} over
                    </span>
                  )}
                </div>
              )}
            </div>
          );
        })}
      </div>

      {/* Daily Totals & Remaining/Overage Banner */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-space-xs pt-space-xs border-t border-surface-container">
        <div className="flex items-baseline gap-2">
          <span className="font-label-sm text-label-sm text-on-surface-variant font-semibold">
            Estimated Daily Total:
          </span>
          <span className="font-metric-num text-base font-bold text-primary">
            {summary.is_complete && summary.daily_total_cost !== null && summary.daily_total_cost !== undefined
              ? `₹${summary.daily_total_cost.toFixed(2)}`
              : `${summary.partial_cost_formatted || "Estimate incomplete"} (Partial)`}
          </span>
          {!summary.is_complete && (
            <span className="font-body-sm text-[11px] text-amber-700 italic">
              ({summary.incomplete_slots.length} slot with incomplete prices)
            </span>
          )}
        </div>

        {/* Budget Comparison Banner */}
        {isPerDay && (
          <div>
            {summary.is_complete ? (
              summary.is_over_budget ? (
                <div className="flex items-center gap-1.5 px-3 py-1 rounded-full bg-error/10 text-error font-label-sm text-label-sm font-bold">
                  <span className="material-symbols-outlined text-[15px]">trending_up</span>
                  <span>Exceeds daily budget by ₹{summary.overage_amount.toFixed(2)}</span>
                </div>
              ) : (
                <div className="flex items-center gap-1.5 px-3 py-1 rounded-full bg-secondary/15 text-secondary font-label-sm text-label-sm font-bold">
                  <span className="material-symbols-outlined text-[15px]">savings</span>
                  <span>₹{summary.remaining_budget?.toFixed(2)} remaining under budget</span>
                </div>
              )
            ) : (
              <div className="font-body-sm text-[11px] text-on-surface-variant italic">
                Remaining budget unavailable until all meal prices are complete.
              </div>
            )}
          </div>
        )}
      </div>
    </div>
  );
};
