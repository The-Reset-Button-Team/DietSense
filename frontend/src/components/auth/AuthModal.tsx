"use client";

import React, { useState } from "react";
import { useAuth } from "@/context/AuthContext";
import { GoalType } from "@/types";

interface AuthModalProps {
  isOpen: boolean;
  onClose: () => void;
}

export const AuthModal: React.FC<AuthModalProps> = ({ isOpen, onClose }) => {
  const { user, login, register, logout, isAuthenticated } = useAuth();
  const [isRegisterMode, setIsRegisterMode] = useState(false);
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [name, setName] = useState("");
  const [goal, setGoal] = useState<GoalType>("lose_weight");
  const [weight, setWeight] = useState(75);
  const [height, setHeight] = useState(175);
  const [age, setAge] = useState(26);

  if (!isOpen) return null;

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (isRegisterMode) {
      await register({
        email,
        full_name: name || email.split("@")[0],
        goal,
        weight_kg: weight,
        height_cm: height,
        age,
      });
    } else {
      await login(email || "arvykrane@dietsense.ai", password || "password123");
    }
    onClose();
  };

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/40 backdrop-blur-sm animate-fade-in">
      <div className="relative w-full max-w-md bg-[#faf7f2] border border-[#e2d6c9] rounded-3xl p-6 sm:p-8 shadow-2xl overflow-hidden">
        
        {/* Atmosphere Light */}
        <div className="absolute -top-16 -right-12 w-48 h-48 bg-[#dbeafe] rounded-full blur-2xl pointer-events-none opacity-60"></div>
        <div className="absolute -bottom-16 -left-12 w-48 h-48 bg-[#fce7f3] rounded-full blur-2xl pointer-events-none opacity-60"></div>

        {/* Close Button */}
        <button
          onClick={onClose}
          className="absolute top-5 right-5 w-8 h-8 rounded-full bg-white/80 border border-slate-200 text-slate-500 hover:text-slate-800 flex items-center justify-center text-sm font-bold shadow-sm"
        >
          ✕
        </button>

        {isAuthenticated ? (
          <div className="space-y-5 text-center relative z-10">
            <div className="w-16 h-16 rounded-full bg-[#eff6ff] border-2 border-[#1d4ed8] text-[#1d4ed8] font-bold text-2xl flex items-center justify-center mx-auto shadow-sm">
              {user?.full_name?.charAt(0).toUpperCase() || "A"}
            </div>
            <div>
              <h2 className="text-xl font-serif font-bold text-[#421018]">
                {user?.full_name || "arvykrane"}
              </h2>
              <p className="text-xs text-slate-500 font-mono mt-0.5">{user?.email}</p>
              <div className="inline-flex items-center gap-2 px-3 py-1 mt-2.5 rounded-full bg-[#f3eae0] border border-[#d8c8b8] text-[11px] font-semibold text-[#581825]">
                <span>🎯 Goal: {user?.goal?.replace("_", " ")}</span>
                <span>•</span>
                <span>🔥 {user?.daily_calorie_target} kcal</span>
              </div>
            </div>

            <div className="pt-2 border-t border-[#e8ded3] flex gap-3">
              <button
                onClick={onClose}
                className="flex-1 py-2.5 rounded-xl bg-[#581825] text-white text-xs font-semibold hover:bg-[#421018] shadow-sm transition-all"
              >
                Continue to Dashboard
              </button>
              <button
                onClick={() => {
                  logout();
                  onClose();
                }}
                className="px-4 py-2.5 rounded-xl bg-white border border-red-200 text-red-700 text-xs font-semibold hover:bg-red-50 shadow-sm transition-all"
              >
                Sign Out
              </button>
            </div>
          </div>
        ) : (
          <form onSubmit={handleSubmit} className="space-y-4 relative z-10">
            <div>
              <span className="text-[10px] font-bold uppercase tracking-wider text-[#581825] bg-[#f3eae0] px-2.5 py-0.5 rounded-full border border-[#d8c8b8]">
                DietSense Account
              </span>
              <h2 className="text-2xl font-serif font-bold text-[#421018] mt-1.5">
                {isRegisterMode ? "Create Your Profile" : "Welcome Back"}
              </h2>
              <p className="text-xs text-slate-600 font-light mt-0.5">
                {isRegisterMode
                  ? "Save your biometrics, grocery inventory, and solo-cooking routine."
                  : "Sign in to access your synchronized meal plans and verified recipes."}
              </p>
            </div>

            {isRegisterMode && (
              <div>
                <label className="block text-[11px] font-semibold text-slate-700 mb-1">Your Name</label>
                <input
                  type="text"
                  required
                  value={name}
                  onChange={(e) => setName(e.target.value)}
                  placeholder="e.g. Arvy"
                  className="w-full px-3.5 py-2 rounded-xl bg-white border border-[#d8c8b8] text-xs text-slate-800 focus:outline-none focus:ring-2 focus:ring-[#1d4ed8]"
                />
              </div>
            )}

            <div>
              <label className="block text-[11px] font-semibold text-slate-700 mb-1">Email Address</label>
              <input
                type="email"
                required
                value={email}
                onChange={(e) => setEmail(e.target.value)}
                placeholder="you@example.com"
                className="w-full px-3.5 py-2 rounded-xl bg-white border border-[#d8c8b8] text-xs text-slate-800 focus:outline-none focus:ring-2 focus:ring-[#1d4ed8]"
              />
            </div>

            <div>
              <label className="block text-[11px] font-semibold text-slate-700 mb-1">Password</label>
              <input
                type="password"
                required
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                placeholder="••••••••"
                className="w-full px-3.5 py-2 rounded-xl bg-white border border-[#d8c8b8] text-xs text-slate-800 focus:outline-none focus:ring-2 focus:ring-[#1d4ed8]"
              />
            </div>

            {isRegisterMode && (
              <div className="grid grid-cols-3 gap-2 pt-1">
                <div>
                  <label className="block text-[10px] font-semibold text-slate-600 mb-0.5">Weight (kg)</label>
                  <input
                    type="number"
                    value={weight}
                    onChange={(e) => setWeight(Number(e.target.value))}
                    className="w-full px-2.5 py-1.5 rounded-lg bg-white border border-[#d8c8b8] text-xs"
                  />
                </div>
                <div>
                  <label className="block text-[10px] font-semibold text-slate-600 mb-0.5">Height (cm)</label>
                  <input
                    type="number"
                    value={height}
                    onChange={(e) => setHeight(Number(e.target.value))}
                    className="w-full px-2.5 py-1.5 rounded-lg bg-white border border-[#d8c8b8] text-xs"
                  />
                </div>
                <div>
                  <label className="block text-[10px] font-semibold text-slate-600 mb-0.5">Age</label>
                  <input
                    type="number"
                    value={age}
                    onChange={(e) => setAge(Number(e.target.value))}
                    className="w-full px-2.5 py-1.5 rounded-lg bg-white border border-[#d8c8b8] text-xs"
                  />
                </div>
              </div>
            )}

            <button
              type="submit"
              className="w-full py-2.5 rounded-xl bg-[#581825] text-white text-xs font-semibold hover:bg-[#421018] shadow-md transition-all mt-2"
            >
              {isRegisterMode ? "Register & Setup Plan" : "Sign In"}
            </button>

            <div className="text-center pt-2">
              <button
                type="button"
                onClick={() => setIsRegisterMode(!isRegisterMode)}
                className="text-xs text-[#1d4ed8] hover:underline font-medium"
              >
                {isRegisterMode
                  ? "Already have an account? Sign In"
                  : "Don't have an account? Create one"}
              </button>
            </div>
          </form>
        )}
      </div>
    </div>
  );
};
