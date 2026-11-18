"use client";

import React, { useState } from "react";
import Image from "next/image";
import { useAuth } from "@/context/AuthContext";

export const ProgressAnalytics: React.FC = () => {
  const { user } = useAuth();
  const [filter, setFilter] = useState<"all" | "eaten" | "skipped">("all");
  const [searchQuery, setSearchQuery] = useState("");

  const logs = [
    {
      id: 1,
      time: "Today, 20:15",
      date: "Oct 24, 2026",
      name: "Yellow Dal Tadka & Brown Rice",
      slot: "Dinner",
      cals: 440,
      protein: 22,
      carbs: 68,
      fat: 9,
      outcome: "eaten",
      reason: "Eaten & Logged",
      notes: "Satiety felt steady, no post-meal energy crash. ICMR-NIN verified.",
      img: "/stitch/assets/stitch_asset_06.png",
    },
    {
      id: 2,
      time: "Today, 13:40",
      date: "Oct 24, 2026",
      name: "Paneer Bhurji & Multigrain Roti",
      slot: "Lunch",
      cals: 540,
      protein: 38,
      carbs: 46,
      fat: 16,
      outcome: "eaten",
      reason: "Eaten & Logged",
      notes: "Quick 15 min solo skillet prep. High protein score maintained.",
      img: "/stitch/assets/stitch_asset_03.png",
    },
    {
      id: 3,
      time: "Yesterday, 20:30",
      date: "Oct 23, 2026",
      name: "Slow-Simmered Rajma Masala & Quinoa",
      slot: "Dinner",
      cals: 490,
      protein: 24,
      carbs: 72,
      fat: 8,
      outcome: "skipped",
      reason: "Time (Prep > 35m)",
      notes: "Work call ran late, opted for quick Greek yogurt & toasted chana.",
      img: "/stitch/assets/stitch_asset_01.png",
    },
    {
      id: 4,
      time: "Yesterday, 17:00",
      date: "Oct 23, 2026",
      name: "Roasted Makhana & Cardamom Chai",
      slot: "Snack",
      cals: 195,
      protein: 11,
      carbs: 22,
      fat: 4,
      outcome: "eaten",
      reason: "Eaten & Logged",
      notes: "Low glycemic buffer maintained, prevented evening binge.",
      img: "/stitch/assets/stitch_asset_08.png",
    },
    {
      id: 5,
      time: "Oct 22, 13:30",
      date: "Oct 22, 2026",
      name: "Grilled Chicken & Avocado Salad",
      slot: "Lunch",
      cals: 460,
      protein: 42,
      carbs: 18,
      fat: 20,
      outcome: "eaten",
      reason: "Eaten & Logged",
      notes: "Pantry in-stock match, verified USDA SR-Legacy data.",
      img: "/stitch/assets/stitch_asset_11.png",
    },
    {
      id: 6,
      time: "Oct 21, 20:45",
      date: "Oct 21, 2026",
      name: "Palak Paneer Gravy with Millet Roti",
      slot: "Dinner",
      cals: 510,
      protein: 32,
      carbs: 48,
      fat: 18,
      outcome: "skipped",
      reason: "Missing Groceries",
      notes: "Blender was unwashed, skipped pureed spinach step.",
      img: "/stitch/assets/stitch_asset_07.png",
    },
  ];

  const filteredLogs = logs.filter((log) => {
    if (filter !== "all" && log.outcome !== filter) return false;
    if (searchQuery) {
      const q = searchQuery.toLowerCase();
      return (
        log.name.toLowerCase().includes(q) ||
        log.notes.toLowerCase().includes(q) ||
        log.slot.toLowerCase().includes(q)
      );
    }
    return true;
  });

  return (
    <div className="space-y-space-lg pb-16">
      {/* Editorial Header */}
      <div className="flex flex-col lg:flex-row lg:items-end justify-between gap-space-md pt-space-xs pb-space-sm border-b border-surface-container-highest">
        <div className="space-y-1">
          <div className="flex items-center gap-space-xs text-primary">
            <span className="material-symbols-outlined text-[18px]">monitoring</span>
            <span className="font-label-sm text-label-sm uppercase tracking-wider text-primary font-bold">
              Quantitative Biometrics • Weekly Cohort
            </span>
          </div>
          <h1 className="font-headline-lg text-headline-lg text-primary tracking-tight font-serif">
            Biometric Adherence &amp; Behavioral Feedback
          </h1>
          <p className="font-body-md text-body-md text-on-surface-variant max-w-2xl">
            Empirical adherence metrics and skip-feedback analysis. When friction is detected, the
            adaptive engine recalibrates recommendation weights without cloud latency.
          </p>
        </div>

        <div className="flex items-center gap-2">
          <button
            type="button"
            className="px-space-md py-2 bg-surface-container hover:bg-surface-container-high text-primary rounded font-label-md text-label-md transition-all flex items-center gap-1.5 border border-surface-container"
          >
            <span className="material-symbols-outlined text-[18px]">file_download</span>
            Export Clinical Report
          </button>
        </div>
      </div>

      {/* KPI 4-Card Summary Spread */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-space-md">
        {/* KPI 1 */}
        <div className="bg-surface-container-lowest p-space-lg rounded-xl shadow-sm border border-surface-container space-y-1">
          <div className="flex items-center justify-between text-on-surface-variant">
            <span className="font-label-sm text-label-sm uppercase tracking-wide font-bold">
              14-Day Adherence
            </span>
            <span className="material-symbols-outlined text-[20px] text-secondary">verified</span>
          </div>
          <div className="flex items-baseline gap-1.5 pt-1">
            <span className="font-metric-num text-[32px] text-primary">82.5%</span>
            <span className="font-label-sm text-label-sm text-secondary font-bold">
              +4.2% vs last wk
            </span>
          </div>
          <p className="text-body-sm text-on-surface-variant">42 of 51 prescribed slots executed</p>
          <div className="pt-2">
            <span className="font-label-sm text-label-sm bg-secondary/10 text-secondary px-2 py-0.5 rounded-full font-bold">
              Tier 1 Consistency
            </span>
          </div>
        </div>

        {/* KPI 2 */}
        <div className="bg-surface-container-lowest p-space-lg rounded-xl shadow-sm border border-surface-container space-y-1">
          <div className="flex items-center justify-between text-on-surface-variant">
            <span className="font-label-sm text-label-sm uppercase tracking-wide font-bold">
              Calorie Cut Deficit
            </span>
            <span className="material-symbols-outlined text-[20px] text-primary">
              local_fire_department
            </span>
          </div>
          <div className="flex items-baseline gap-1.5 pt-1">
            <span className="font-metric-num text-[32px] text-primary">-385</span>
            <span className="font-label-sm text-label-sm text-on-surface-variant">kcal / day avg</span>
          </div>
          <p className="text-body-sm text-on-surface-variant">Within 3.8% of -400 kcal clinical goal</p>
          <div className="pt-2">
            <span className="font-label-sm text-label-sm bg-primary/10 text-primary px-2 py-0.5 rounded-full font-bold">
              Target Met (96%)
            </span>
          </div>
        </div>

        {/* KPI 3 */}
        <div className="bg-surface-container-lowest p-space-lg rounded-xl shadow-sm border border-surface-container space-y-1">
          <div className="flex items-center justify-between text-on-surface-variant">
            <span className="font-label-sm text-label-sm uppercase tracking-wide font-bold">
              Glycemic Stability
            </span>
            <span className="material-symbols-outlined text-[20px] text-amber-600">bolt</span>
          </div>
          <div className="flex items-baseline gap-1.5 pt-1">
            <span className="font-metric-num text-[32px] text-on-surface">8.4</span>
            <span className="font-body-sm text-body-sm text-on-surface-variant">/ 10 index</span>
          </div>
          <p className="text-body-sm text-on-surface-variant">Low post-prandial glycemic load</p>
          <div className="pt-2">
            <span className="font-label-sm text-label-sm bg-secondary-container/40 text-secondary px-2 py-0.5 rounded-full font-bold">
              Optimal Cadence
            </span>
          </div>
        </div>

        {/* KPI 4 */}
        <div className="bg-surface-container-lowest p-space-lg rounded-xl shadow-sm border border-surface-container space-y-1">
          <div className="flex items-center justify-between text-on-surface-variant">
            <span className="font-label-sm text-label-sm uppercase tracking-wide font-bold">
              Top Skip Friction
            </span>
            <span className="material-symbols-outlined text-[20px] text-error">
              hourglass_disabled
            </span>
          </div>
          <div className="flex flex-col pt-1">
            <span className="font-headline-sm text-headline-sm text-primary leading-tight font-serif">
              Time (&gt;30m Prep)
            </span>
            <span className="font-label-md text-label-md text-error font-bold mt-0.5">
              55% of all recorded skips
            </span>
          </div>
          <p className="text-body-sm text-on-surface-variant">Auto ML suppression active</p>
          <div className="pt-2">
            <span className="font-label-sm text-label-sm bg-error-container text-on-error-container px-2 py-0.5 rounded-full font-bold">
              Action Taken (+0.2 Bias)
            </span>
          </div>
        </div>
      </div>

      {/* Trajectory & Skip Distribution Spread (8:4 Desktop Split) */}
      <div className="grid grid-cols-1 lg:grid-cols-12 gap-space-lg">
        {/* Chart A: 14-Day Dual-Series Bar Chart */}
        <div className="lg:col-span-8 bg-surface-container-lowest p-space-lg md:p-space-xl rounded-xl shadow-sm border border-surface-container flex flex-col justify-between">
          <div>
            <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-space-xs pb-space-md border-b border-surface-container">
              <div>
                <div className="flex items-center gap-2">
                  <span className="material-symbols-outlined text-[20px] text-primary">
                    bar_chart
                  </span>
                  <h2 className="font-headline-sm text-headline-sm text-primary font-serif">
                    14-Day Daily Adherence Trajectory
                  </h2>
                </div>
                <p className="font-body-sm text-body-sm text-on-surface-variant mt-0.5">
                  Observed meal outcomes: Planned vs Actual execution across daily slots
                </p>
              </div>

              <div className="flex items-center gap-space-md text-label-sm font-label-sm">
                <span className="flex items-center gap-1.5 text-on-surface">
                  <span className="w-3 h-3 rounded-sm bg-primary-container" /> Eaten Meals
                </span>
                <span className="flex items-center gap-1.5 text-on-surface">
                  <span className="w-3 h-3 rounded-sm bg-on-primary-container" /> Skipped Meals
                </span>
              </div>
            </div>

            {/* SVG Visual Chart */}
            <div className="relative w-full h-64 pt-space-md">
              <svg
                aria-label="14-Day Adherence dual bar chart"
                className="w-full h-full overflow-visible"
                preserveAspectRatio="none"
                viewBox="0 0 700 240"
              >
                <line
                  className="text-surface-variant"
                  stroke="currentColor"
                  strokeDasharray="3,3"
                  strokeWidth="1"
                  x1="40"
                  x2="690"
                  y1="20"
                  y2="20"
                />
                <line
                  className="text-surface-variant"
                  stroke="currentColor"
                  strokeDasharray="3,3"
                  strokeWidth="1"
                  x1="40"
                  x2="690"
                  y1="70"
                  y2="70"
                />
                <line
                  className="text-surface-variant"
                  stroke="currentColor"
                  strokeDasharray="3,3"
                  strokeWidth="1"
                  x1="40"
                  x2="690"
                  y1="120"
                  y2="120"
                />
                <line
                  className="text-surface-variant"
                  stroke="currentColor"
                  strokeDasharray="3,3"
                  strokeWidth="1"
                  x1="40"
                  x2="690"
                  y1="170"
                  y2="170"
                />
                <line
                  className="text-outline-variant"
                  stroke="currentColor"
                  strokeWidth="1.5"
                  x1="40"
                  x2="690"
                  y1="210"
                  y2="210"
                />

                <text
                  className="text-[11px] font-label-sm fill-on-surface-variant"
                  textAnchor="end"
                  x="30"
                  y="24"
                >
                  4 slots
                </text>
                <text
                  className="text-[11px] font-label-sm fill-on-surface-variant"
                  textAnchor="end"
                  x="30"
                  y="74"
                >
                  3 slots
                </text>
                <text
                  className="text-[11px] font-label-sm fill-on-surface-variant"
                  textAnchor="end"
                  x="30"
                  y="124"
                >
                  2 slots
                </text>
                <text
                  className="text-[11px] font-label-sm fill-on-surface-variant"
                  textAnchor="end"
                  x="30"
                  y="174"
                >
                  1 slot
                </text>
                <text
                  className="text-[11px] font-label-sm fill-on-surface-variant"
                  textAnchor="end"
                  x="30"
                  y="214"
                >
                  0
                </text>

                {/* 14 Day Bars (Grouped: Eaten / Skipped) */}
                {[
                  { day: "01", eaten: 4, skipped: 0 },
                  { day: "02", eaten: 3, skipped: 1 },
                  { day: "03", eaten: 4, skipped: 0 },
                  { day: "04", eaten: 3, skipped: 1 },
                  { day: "05", eaten: 4, skipped: 0 },
                  { day: "06", eaten: 2, skipped: 2 },
                  { day: "07", eaten: 4, skipped: 0 },
                  { day: "08", eaten: 4, skipped: 0 },
                  { day: "09", eaten: 3, skipped: 1 },
                  { day: "10", eaten: 4, skipped: 0 },
                  { day: "11", eaten: 4, skipped: 0 },
                  { day: "12", eaten: 3, skipped: 1 },
                  { day: "13", eaten: 4, skipped: 0 },
                  { day: "14*", eaten: 4, skipped: 0, isToday: true },
                ].map((d, i) => {
                  const xBase = 58 + i * 44;
                  const eatenHeight = (d.eaten / 4) * 185;
                  const eatenY = 210 - eatenHeight;
                  const skipHeight = (d.skipped / 4) * 185;
                  const skipY = 210 - skipHeight;

                  return (
                    <g key={d.day} className="cursor-pointer group">
                      <rect
                        fill={d.isToday ? "#006c49" : "#581825"}
                        height={eatenHeight}
                        rx="2"
                        width="14"
                        x={xBase}
                        y={eatenY}
                        className="transition-opacity hover:opacity-85"
                      />
                      {d.skipped > 0 && (
                        <rect
                          fill="#d77d89"
                          height={skipHeight}
                          rx="2"
                          width="10"
                          x={xBase + 16}
                          y={skipY}
                          className="transition-opacity hover:opacity-85"
                        />
                      )}
                      <text
                        className={`text-[10px] font-label-sm ${
                          d.isToday ? "fill-secondary font-bold" : "fill-on-surface-variant"
                        }`}
                        textAnchor="middle"
                        x={xBase + 8}
                        y="228"
                      >
                        {d.day}
                      </text>
                    </g>
                  );
                })}
              </svg>
            </div>
          </div>

          <div className="flex items-center justify-between pt-space-sm border-t border-surface-container text-body-sm font-body-sm text-on-surface-variant">
            <span className="flex items-center gap-1">
              <span className="material-symbols-outlined text-[16px] text-secondary">
                check_circle
              </span>
              High compliance run: Days 07–11 recorded zero deviations.
            </span>
            <span className="font-label-sm text-label-sm italic text-outline">
              Target threshold: 80% minimum
            </span>
          </div>
        </div>

        {/* Chart B: Skip Root Causes Donut */}
        <div className="lg:col-span-4 bg-surface-container-lowest p-space-lg md:p-space-xl rounded-xl shadow-sm border border-surface-container flex flex-col justify-between">
          <div>
            <div className="flex items-center justify-between pb-space-xs border-b border-surface-container">
              <div className="flex items-center gap-2">
                <span className="material-symbols-outlined text-[20px] text-error">pie_chart</span>
                <h2 className="font-headline-sm text-headline-sm text-primary font-serif">
                  Skip Root Causes
                </h2>
              </div>
              <span className="font-label-sm text-label-sm text-on-surface-variant bg-surface-container px-2 py-0.5 rounded-full">
                N = 9 Skips
              </span>
            </div>

            <p className="font-body-sm text-body-sm text-on-surface-variant pt-2">
              Qualitative tagging attributed during daily check-ins
            </p>

            {/* Radial SVG Donut */}
            <div className="relative w-44 h-44 mx-auto my-space-md flex items-center justify-center">
              <svg className="w-full h-full -rotate-90" viewBox="0 0 120 120">
                <circle
                  cx="60"
                  cy="60"
                  fill="transparent"
                  r="44"
                  stroke="#581825"
                  strokeWidth="16"
                  strokeDasharray="152.05 124.41"
                  strokeDashoffset="0"
                />
                <circle
                  cx="60"
                  cy="60"
                  fill="transparent"
                  r="44"
                  stroke="#d77d89"
                  strokeWidth="16"
                  strokeDasharray="69.11 207.35"
                  strokeDashoffset="-152.05"
                />
                <circle
                  cx="60"
                  cy="60"
                  fill="transparent"
                  r="44"
                  stroke="#CA8A04"
                  strokeWidth="16"
                  strokeDasharray="33.17 243.29"
                  strokeDashoffset="-221.16"
                />
                <circle
                  cx="60"
                  cy="60"
                  fill="transparent"
                  r="44"
                  stroke="#867274"
                  strokeWidth="16"
                  strokeDasharray="22.12 254.34"
                  strokeDashoffset="-254.33"
                />
              </svg>
              <div className="absolute flex flex-col items-center justify-center text-center">
                <span className="font-metric-num text-[24px] leading-7 text-primary">55%</span>
                <span className="font-label-sm text-[10px] uppercase tracking-wider text-on-surface-variant font-bold">
                  Prep Time
                </span>
              </div>
            </div>

            {/* Breakdown List */}
            <div className="space-y-2 mt-space-sm text-body-sm">
              <div className="flex items-center justify-between p-2 rounded bg-surface-container-low border border-surface-container">
                <div className="flex items-center gap-2">
                  <span className="w-3 h-3 rounded-sm bg-primary-container" />
                  <span className="font-label-md text-label-md text-on-surface">
                    Time Constraints (&gt;30m)
                  </span>
                </div>
                <span className="font-label-md text-label-md font-bold text-primary">
                  55% (5 skips)
                </span>
              </div>

              <div className="flex items-center justify-between p-2 rounded bg-surface-container-low border border-surface-container">
                <div className="flex items-center gap-2">
                  <span className="w-3 h-3 rounded-sm bg-on-primary-container" />
                  <span className="font-label-md text-label-md text-on-surface">
                    Missing Pantry Stock
                  </span>
                </div>
                <span className="font-label-md text-label-md font-bold text-on-surface">
                  25% (2 skips)
                </span>
              </div>

              <div className="flex items-center justify-between p-2 rounded bg-surface-container-low border border-surface-container">
                <div className="flex items-center gap-2">
                  <span className="w-3 h-3 rounded-sm bg-[#CA8A04]" />
                  <span className="font-label-md text-label-md text-on-surface">
                    Budget / Unit Cost
                  </span>
                </div>
                <span className="font-label-md text-label-md font-bold text-on-surface">
                  12% (1 skip)
                </span>
              </div>

              <div className="flex items-center justify-between p-2 rounded bg-surface-container-low border border-surface-container">
                <div className="flex items-center gap-2">
                  <span className="w-3 h-3 rounded-sm bg-outline" />
                  <span className="font-label-md text-label-md text-on-surface">
                    Taste / Appetite Mismatch
                  </span>
                </div>
                <span className="font-label-md text-label-md font-bold text-on-surface">
                  8% (1 skip)
                </span>
              </div>
            </div>
          </div>
        </div>
      </div>

      {/* DietSense ML Adaptive Loop Banner */}
      <div className="bg-surface-container-high rounded-xl p-space-lg shadow-sm border border-surface-container-highest flex flex-col md:flex-row items-start md:items-center justify-between gap-space-md">
        <div className="flex items-start gap-space-md max-w-4xl">
          <div className="w-10 h-10 rounded-full bg-primary-container text-on-primary flex items-center justify-center shrink-0 shadow-sm">
            <span className="material-symbols-outlined text-[22px]">smart_toy</span>
          </div>
          <div className="space-y-1">
            <div className="flex items-center gap-space-xs flex-wrap">
              <span className="font-label-sm text-label-sm font-bold uppercase tracking-wider text-primary">
                DietSense ML Adaptive Loop in Action
              </span>
              <span className="px-2 py-0.5 rounded-full bg-secondary-container text-on-secondary-fixed text-label-sm font-label-sm font-semibold">
                Active Parameter: Bias_PrepTime_Adjust
              </span>
            </div>
            <p className="font-body-md text-body-md text-on-surface leading-snug">
              System detected <strong>5 meal skips</strong> attributable to dinner prep friction.
              The ML scoring engine automatically applied a{" "}
              <strong>+0.2 prep-time penalty</strong> to meals exceeding 25 minutes, re-ranking fast
              15-minute one-pan recipes to the top of your weekly rotation.
            </p>
          </div>
        </div>
      </div>

      {/* Recent Meal Log History Table */}
      <div className="bg-surface-container-lowest rounded-xl shadow-sm border border-surface-container overflow-hidden">
        <div className="p-space-lg flex flex-col md:flex-row md:items-center justify-between gap-space-md bg-surface-container-lowest border-b border-surface-container">
          <div>
            <div className="flex items-center gap-2">
              <span className="material-symbols-outlined text-[20px] text-primary">
                history_edu
              </span>
              <h2 className="font-headline-sm text-headline-sm text-primary font-serif">
                Recent Meal Log Audit History
              </h2>
            </div>
            <p className="font-body-sm text-body-sm text-on-surface-variant mt-0.5">
              Immutable transaction records synced across local SQLite and Supabase cloud
            </p>
          </div>

          <div className="flex items-center gap-space-xs flex-wrap">
            <div className="relative">
              <input
                type="text"
                value={searchQuery}
                onChange={(e) => setSearchQuery(e.target.value)}
                placeholder="Filter meal or notes..."
                className="pl-8 pr-3 py-1.5 bg-surface text-on-surface placeholder:text-outline text-label-md font-label-md rounded focus:outline-none focus:ring-1 focus:ring-primary w-48 sm:w-60 border border-surface-container"
              />
              <span className="material-symbols-outlined text-[16px] text-outline-variant absolute left-2.5 top-2">
                search
              </span>
            </div>

            <div className="flex items-center bg-surface-container rounded p-0.5">
              {(["all", "eaten", "skipped"] as const).map((mode) => (
                <button
                  key={mode}
                  type="button"
                  onClick={() => setFilter(mode)}
                  className={`px-3 py-1 text-label-sm font-label-sm rounded capitalize ${
                    filter === mode
                      ? "bg-surface-container-lowest text-primary font-bold shadow-sm"
                      : "text-on-surface-variant hover:text-on-surface"
                  }`}
                >
                  {mode === "all" ? `All Logs (${logs.length})` : mode}
                </button>
              ))}
            </div>
          </div>
        </div>

        {/* Responsive Table */}
        <div className="overflow-x-auto">
          <table className="w-full text-left border-collapse">
            <thead>
              <tr className="bg-surface-container-low text-on-surface-variant font-label-sm text-label-sm uppercase tracking-wider border-b border-surface-container">
                <th className="py-3 px-space-lg font-semibold">Date &amp; Time</th>
                <th className="py-3 px-space-md font-semibold">Meal Name &amp; Profile</th>
                <th className="py-3 px-space-md font-semibold">Slot</th>
                <th className="py-3 px-space-md font-semibold text-right">Calorie Impact</th>
                <th className="py-3 px-space-md font-semibold">Outcome &amp; Reason</th>
                <th className="py-3 px-space-lg font-semibold">Clinical Feedback / Notes</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-surface-container text-body-sm font-body-sm text-on-surface">
              {filteredLogs.map((log) => (
                <tr
                  key={log.id}
                  className="hover:bg-surface-container-low/50 transition-colors"
                >
                  <td className="py-3 px-space-lg whitespace-nowrap text-on-surface-variant">
                    <span className="font-label-md text-label-md text-on-surface block font-bold">
                      {log.time}
                    </span>
                    <span className="font-label-sm text-label-sm text-outline">{log.date}</span>
                  </td>

                  <td className="py-3 px-space-md">
                    <div className="flex items-center gap-space-sm">
                      <div className="relative w-10 h-10 rounded overflow-hidden shrink-0 bg-surface-container border border-surface-container">
                        <Image
                          src={log.img}
                          alt={log.name}
                          fill
                          className="object-cover"
                          sizes="40px"
                        />
                      </div>
                      <div>
                        <div className="font-label-lg text-label-lg text-primary font-bold font-serif">
                          {log.name}
                        </div>
                        <div className="flex items-center gap-1.5 mt-0.5">
                          <span className="text-[10px] font-label-sm px-1.5 py-0.2 rounded bg-surface-container font-medium text-on-surface-variant">
                            P: {log.protein}g
                          </span>
                          <span className="text-[10px] font-label-sm px-1.5 py-0.2 rounded bg-surface-container font-medium text-on-surface-variant">
                            C: {log.carbs}g
                          </span>
                          <span className="text-[10px] font-label-sm px-1.5 py-0.2 rounded bg-surface-container font-medium text-on-surface-variant">
                            F: {log.fat}g
                          </span>
                        </div>
                      </div>
                    </div>
                  </td>

                  <td className="py-3 px-space-md">
                    <span className="font-label-sm text-label-sm bg-surface-container text-on-surface px-2 py-0.5 rounded font-medium">
                      {log.slot}
                    </span>
                  </td>

                  <td className="py-3 px-space-md text-right font-metric-num text-[15px] font-bold text-on-surface">
                    {log.cals} kcal
                  </td>

                  <td className="py-3 px-space-md whitespace-nowrap">
                    {log.outcome === "eaten" ? (
                      <span className="inline-flex items-center gap-1 px-2.5 py-0.5 rounded-full bg-secondary-container/40 text-secondary font-label-sm text-label-sm font-bold">
                        <span className="w-1.5 h-1.5 rounded-full bg-secondary" />
                        {log.reason}
                      </span>
                    ) : (
                      <span className="inline-flex items-center gap-1 px-2.5 py-0.5 rounded-full bg-error-container text-on-error-container font-label-sm text-label-sm font-bold">
                        <span className="w-1.5 h-1.5 rounded-full bg-error" />
                        {log.reason}
                      </span>
                    )}
                  </td>

                  <td className="py-3 px-space-lg text-on-surface-variant max-w-xs">
                    {log.notes}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );
};
