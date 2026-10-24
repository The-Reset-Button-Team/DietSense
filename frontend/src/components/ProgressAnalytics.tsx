"use client";

import React, { useState, useEffect } from "react";
import {
  ResponsiveContainer,
  BarChart,
  Bar,
  XAxis,
  YAxis,
  Tooltip,
  CartesianGrid,
  Legend,
  PieChart,
  Pie,
  Cell,
} from "recharts";
import { apiClient } from "@/lib/api-client";
import { useAuth } from "@/context/AuthContext";

interface AnalyticsData {
  total_logged: number;
  eaten_count: number;
  skipped_count: number;
  adherence_rate_pct: number;
  skip_reasons: Record<string, number>;
  daily_trends: Array<{ date: string; eaten: number; skipped: number }>;
  has_data: boolean;
}

const COLORS = ["#10b981", "#ef4444", "#f59e0b", "#6366f1", "#8b5cf6"];
const SKIP_REASON_COLORS: Record<string, string> = {
  time: "#f59e0b",
  cost: "#3b82f6",
  taste: "#ec4899",
  unavailable: "#8b5cf6",
};

export const ProgressAnalytics: React.FC = () => {
  const { isAuthenticated } = useAuth();
  const [data, setData] = useState<AnalyticsData | null>(null);
  const [isLoading, setIsLoading] = useState<boolean>(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    let mounted = true;
    async function fetchAnalytics() {
      setIsLoading(true);
      setError(null);
      try {
        const result = await apiClient<AnalyticsData>("/analytics");
        if (mounted) {
          setData(result);
        }
      } catch (err: any) {
        if (mounted) {
          // If not authenticated or backend unavailable, set empty state
          setData({
            total_logged: 0,
            eaten_count: 0,
            skipped_count: 0,
            adherence_rate_pct: 0.0,
            skip_reasons: { time: 0, cost: 0, taste: 0, unavailable: 0 },
            daily_trends: [],
            has_data: false,
          });
          if (isAuthenticated) {
            setError(err?.message || "Could not load analytics");
          }
        }
      } finally {
        if (mounted) {
          setIsLoading(false);
        }
      }
    }

    fetchAnalytics();
    return () => {
      mounted = false;
    };
  }, [isAuthenticated]);

  if (isLoading) {
    return (
      <div className="p-8 text-center text-xs text-slate-500 bg-white rounded-2xl border border-[#e8ded3]">
        <div className="w-6 h-6 border-2 border-[#581825] border-t-transparent rounded-full animate-spin mx-auto mb-2" />
        <span>Loading adherence and trend analytics...</span>
      </div>
    );
  }

  const hasData = data && data.has_data && data.total_logged > 0;

  const outcomeData = hasData
    ? [
        { name: "Eaten ✓", count: data.eaten_count, fill: "#10b981" },
        { name: "Skipped ✕", count: data.skipped_count, fill: "#f43f5e" },
      ]
    : [];

  const skipReasonData = hasData
    ? Object.entries(data.skip_reasons)
        .filter(([_, count]) => count > 0)
        .map(([reason, count]) => ({
          name: reason.charAt(0).toUpperCase() + reason.slice(1),
          count,
        }))
    : [];

  return (
    <div className="space-y-4">
      {/* Disclaimer Banner per Workflow Brief Section 1 */}
      <div className="p-3.5 rounded-2xl bg-[#faf7f2] border border-[#e2d6c9] flex items-center justify-between text-xs text-slate-600">
        <div className="flex items-center gap-2">
          <span>🛡️</span>
          <span>
            <strong>Dataset Estimates Notice:</strong> Adherence metrics and nutritional values are derived from verified
            USDA &amp; ICMR-NIN datasets. DietSense is not a medical product.
          </span>
        </div>
        <span className="text-[10px] font-mono bg-white px-2 py-0.5 rounded border border-[#d8c8b8] text-slate-500">
          Auditable · No LLM Hallucinations
        </span>
      </div>

      {/* Summary Stat Cards */}
      <div className="grid grid-cols-2 sm:grid-cols-4 gap-3">
        <div className="p-4 rounded-2xl bg-white border border-[#e8ded3] shadow-sm">
          <span className="text-xs text-slate-500 font-medium">Adherence Rate</span>
          <div className="text-2xl font-bold font-serif text-[#421018] mt-1">
            {hasData ? `${data.adherence_rate_pct}%` : "0%"}
          </div>
          <span className="text-[10px] text-slate-400">Target: &gt; 80% weekly</span>
        </div>

        <div className="p-4 rounded-2xl bg-white border border-[#e8ded3] shadow-sm">
          <span className="text-xs text-slate-500 font-medium">Meals Eaten</span>
          <div className="text-2xl font-bold font-serif text-emerald-700 mt-1">
            {hasData ? data.eaten_count : 0}
          </div>
          <span className="text-[10px] text-emerald-600">Maintains current plan</span>
        </div>

        <div className="p-4 rounded-2xl bg-white border border-[#e8ded3] shadow-sm">
          <span className="text-xs text-slate-500 font-medium">Meals Skipped</span>
          <div className="text-2xl font-bold font-serif text-rose-700 mt-1">
            {hasData ? data.skipped_count : 0}
          </div>
          <span className="text-[10px] text-rose-600">Triggers adaptive penalty</span>
        </div>

        <div className="p-4 rounded-2xl bg-white border border-[#e8ded3] shadow-sm">
          <span className="text-xs text-slate-500 font-medium">Total Logged</span>
          <div className="text-2xl font-bold font-serif text-[#1d4ed8] mt-1">
            {hasData ? data.total_logged : 0}
          </div>
          <span className="text-[10px] text-slate-400">Outcome entries</span>
        </div>
      </div>

      {!hasData ? (
        <div className="p-10 rounded-2xl bg-white border border-[#e8ded3] text-center space-y-3 shadow-sm">
          <div className="w-14 h-14 rounded-full bg-[#faf7f2] border border-[#d8c8b8] text-2xl flex items-center justify-center mx-auto">
            📊
          </div>
          <h3 className="text-base font-serif font-bold text-[#421018]">No Meal Logs Yet</h3>
          <p className="text-xs text-slate-600 max-w-md mx-auto leading-relaxed">
            As you mark meals as <strong>Eaten ✓</strong> or <strong>Skipped ✕</strong> on your daily plan,
            real adherence percentages, skip reason breakdowns, and daily trend charts will automatically appear here.
          </p>
        </div>
      ) : (
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          {/* Eaten vs Skipped Bar Chart */}
          <div className="p-4 rounded-2xl bg-white border border-[#e8ded3] shadow-sm space-y-3">
            <h4 className="text-xs font-bold text-[#421018] uppercase tracking-wider">
              Meal Outcomes (Eaten vs Skipped)
            </h4>
            <div className="h-60 w-full">
              <ResponsiveContainer width="100%" height="100%">
                <BarChart data={outcomeData} margin={{ top: 10, right: 10, left: -20, bottom: 5 }}>
                  <CartesianGrid strokeDasharray="3 3" vertical={false} stroke="#f1f5f9" />
                  <XAxis dataKey="name" tick={{ fontSize: 11 }} />
                  <YAxis allowDecimals={false} tick={{ fontSize: 11 }} />
                  <Tooltip />
                  <Bar dataKey="count" radius={[6, 6, 0, 0]}>
                    {outcomeData.map((entry, idx) => (
                      <Cell key={`cell-${idx}`} fill={entry.fill} />
                    ))}
                  </Bar>
                </BarChart>
              </ResponsiveContainer>
            </div>
          </div>

          {/* Skip Reasons Breakdown */}
          <div className="p-4 rounded-2xl bg-white border border-[#e8ded3] shadow-sm space-y-3">
            <h4 className="text-xs font-bold text-[#421018] uppercase tracking-wider">
              Skip Reasons (Adaptive Triggers)
            </h4>
            {skipReasonData.length > 0 ? (
              <div className="h-60 w-full">
                <ResponsiveContainer width="100%" height="100%">
                  <BarChart data={skipReasonData} margin={{ top: 10, right: 10, left: -20, bottom: 5 }}>
                    <CartesianGrid strokeDasharray="3 3" vertical={false} stroke="#f1f5f9" />
                    <XAxis dataKey="name" tick={{ fontSize: 11 }} />
                    <YAxis allowDecimals={false} tick={{ fontSize: 11 }} />
                    <Tooltip />
                    <Bar dataKey="count" fill="#6366f1" radius={[6, 6, 0, 0]}>
                      {skipReasonData.map((entry, idx) => (
                        <Cell
                          key={`cell-skip-${idx}`}
                          fill={SKIP_REASON_COLORS[entry.name.toLowerCase()] || COLORS[idx % COLORS.length]}
                        />
                      ))}
                    </Bar>
                  </BarChart>
                </ResponsiveContainer>
              </div>
            ) : (
              <div className="h-60 flex items-center justify-center text-xs text-slate-400">
                <span>No skipped meals recorded. Great adherence!</span>
              </div>
            )}
          </div>

          {/* Daily Trend Timeline */}
          {data.daily_trends.length > 0 && (
            <div className="md:col-span-2 p-4 rounded-2xl bg-white border border-[#e8ded3] shadow-sm space-y-3">
              <h4 className="text-xs font-bold text-[#421018] uppercase tracking-wider">
                Daily Adherence Timeline (Logged Meals per Day)
              </h4>
              <div className="h-64 w-full">
                <ResponsiveContainer width="100%" height="100%">
                  <BarChart data={data.daily_trends} margin={{ top: 10, right: 20, left: -10, bottom: 5 }}>
                    <CartesianGrid strokeDasharray="3 3" vertical={false} stroke="#f1f5f9" />
                    <XAxis dataKey="date" tick={{ fontSize: 11 }} />
                    <YAxis allowDecimals={false} tick={{ fontSize: 11 }} />
                    <Tooltip />
                    <Legend wrapperStyle={{ fontSize: 11 }} />
                    <Bar dataKey="eaten" name="Eaten" fill="#10b981" stackId="a" radius={[0, 0, 4, 4]} />
                    <Bar dataKey="skipped" name="Skipped" fill="#f43f5e" stackId="a" radius={[4, 4, 0, 0]} />
                  </BarChart>
                </ResponsiveContainer>
              </div>
            </div>
          )}
        </div>
      )}
    </div>
  );
};
