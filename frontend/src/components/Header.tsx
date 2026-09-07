"use client";

import React from "react";
import { GoalType } from "@/types";
import { useAuth } from "@/context/AuthContext";

interface HeaderProps {
  goal: GoalType;
  targetCalories: number;
  onOpenAuth: () => void;
}

export const Header: React.FC<HeaderProps> = ({ goal, targetCalories, onOpenAuth }) => {
  const { user, isAuthenticated } = useAuth();

  return (
    <div className="relative z-10 flex flex-col md:flex-row md:items-center justify-between gap-5 pb-6 border-b border-[#e9dfd5]">
      <div>
        <div className="flex items-center gap-2 mb-2.5">
          <div className="inline-flex items-center gap-2 px-3 py-1 rounded-full bg-[#f3eae0] border border-[#d8c8b8] text-[#581825] text-xs font-medium tracking-wide shadow-sm">
            <span className="w-2 h-2 rounded-full bg-[#581825] animate-pulse"></span>
            <span>DietSense Atmos · Solo Cook & AI Pantry Studio</span>
          </div>

          {/* User Profile Capsule Button */}
          <button
            onClick={onOpenAuth}
            className="inline-flex items-center gap-1.5 px-3 py-1 rounded-full bg-white border border-[#bfdbfe] text-[#1d4ed8] text-xs font-semibold hover:bg-[#eff6ff] transition-all shadow-sm"
          >
            <span className="w-4 h-4 rounded-full bg-[#1d4ed8] text-white flex items-center justify-center text-[9px]">
              {user?.full_name?.charAt(0).toUpperCase() || "A"}
            </span>
            <span>{isAuthenticated ? user?.full_name : "Sign In"}</span>
            <span className="text-[10px] text-slate-400">⚙️</span>
          </button>
        </div>

        <h1 className="text-2xl sm:text-3xl font-serif text-[#421018] tracking-tight">
          Namaste, <span className="text-[#1d4ed8] font-sans font-normal">{user?.full_name || "arvykrane"}</span>
        </h1>
        <p className="text-sm text-slate-600 mt-1 font-light max-w-xl">
          Cook for yourself with zero stress: upload your grocery list, set meal routine, and follow easy Hinglish recipes.
        </p>
      </div>

      {/* Dynamic Target Card */}
      <div className="flex items-center gap-3.5 bg-white/95 border border-[#e2d6c9] rounded-2xl p-3.5 px-5 shadow-sm backdrop-blur-md shrink-0">
        <div className="w-12 h-12 rounded-xl bg-[#eff6ff] border border-[#bfdbfe] flex items-center justify-center text-2xl shrink-0">
          🔥
        </div>
        <div>
          <p className="text-[11px] uppercase tracking-wider text-slate-500 font-semibold">
            {goal === "lose_weight"
              ? "Goal: Cut (-400 kcal)"
              : goal === "gain_weight"
              ? "Goal: Surplus (+300 kcal)"
              : "Goal: Maintain (TDEE)"}
          </p>
          <p className="text-lg text-[#421018] font-serif font-bold">
            {targetCalories.toLocaleString()}{" "}
            <span className="text-xs font-sans text-slate-500 font-normal">kcal / day</span>
          </p>
        </div>
      </div>
    </div>
  );
};
