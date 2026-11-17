"use client";

import React, { useState } from "react";
import { useAuth } from "@/context/AuthContext";
import { GoalType } from "@/types";

interface AuthModalProps {
  isOpen: boolean;
  onClose: () => void;
}

export const AuthModal: React.FC<AuthModalProps> = ({ isOpen, onClose }) => {
  const {
    user,
    login,
    register,
    loginWithSupabase,
    registerWithSupabase,
    linkSupabase,
    unlinkSupabase,
    logout,
    isAuthenticated,
  } = useAuth();

  const [isRegisterMode, setIsRegisterMode] = useState(false);
  const [providerMode, setProviderMode] = useState<"local" | "supabase">("local");
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [name, setName] = useState("");
  const [goal, setGoal] = useState<GoalType>("lose_weight");
  const [weight, setWeight] = useState(75);
  const [height, setHeight] = useState(175);
  const [age, setAge] = useState(26);
  const [errorMessage, setErrorMessage] = useState("");
  const [linkSuccessMessage, setLinkSuccessMessage] = useState("");
  const [isLinking, setIsLinking] = useState(false);
  const [linkEmail, setLinkEmail] = useState("");
  const [linkPassword, setLinkPassword] = useState("");

  if (!isOpen) return null;

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setErrorMessage("");

    let res;
    if (isRegisterMode) {
      const regData = {
        email,
        password,
        full_name: name || email.split("@")[0],
        goal,
        weight_kg: weight,
        height_cm: height,
        age,
      };
      res = providerMode === "supabase"
        ? await registerWithSupabase(regData)
        : await register(regData);
    } else {
      res = providerMode === "supabase"
        ? await loginWithSupabase(email, password)
        : await login(email, password);
    }

    if (res.success) {
      onClose();
    } else {
      setErrorMessage(res.error || "Authentication failed.");
    }
  };

  const handleLinkSupabase = async (e: React.FormEvent) => {
    e.preventDefault();
    setErrorMessage("");
    setLinkSuccessMessage("");
    const res = await linkSupabase({ email: linkEmail, password: linkPassword });
    if (res.success) {
      setLinkSuccessMessage("Supabase account linked successfully!");
      setIsLinking(false);
      setLinkEmail("");
      setLinkPassword("");
    } else {
      setErrorMessage(res.error || "Failed to link Supabase account.");
    }
  };

  const handleUnlinkSupabase = async () => {
    if (!confirm("Are you sure you want to unlink your Supabase account?")) return;
    setErrorMessage("");
    setLinkSuccessMessage("");
    const res = await unlinkSupabase();
    if (res.success) {
      setLinkSuccessMessage("Supabase account unlinked.");
    } else {
      setErrorMessage(res.error || "Failed to unlink Supabase account.");
    }
  };

  const hasLocal = user?.auth_providers?.includes("local") ?? true;
  const hasSupabase = user?.auth_providers?.includes("supabase") ?? false;

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/40 backdrop-blur-sm animate-fade-in">
      <div className="relative w-full max-w-md bg-[#faf7f2] border border-[#e2d6c9] rounded-3xl p-6 sm:p-8 shadow-2xl overflow-hidden max-h-[90vh] overflow-y-auto">
        
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
                {user?.full_name || "DietSense User"}
              </h2>
              <p className="text-xs text-slate-500 font-mono mt-0.5">{user?.email}</p>
              
              {/* Linked Providers */}
              <div className="flex items-center justify-center gap-2 mt-3">
                {hasLocal && (
                  <span className="inline-flex items-center gap-1 px-2.5 py-0.5 rounded-full bg-emerald-50 border border-emerald-200 text-[10px] font-semibold text-emerald-800">
                    ✓ Local Auth
                  </span>
                )}
                {hasSupabase ? (
                  <span className="inline-flex items-center gap-1 px-2.5 py-0.5 rounded-full bg-blue-50 border border-blue-200 text-[10px] font-semibold text-blue-800">
                    ✓ Supabase Linked
                  </span>
                ) : (
                  <span className="inline-flex items-center gap-1 px-2.5 py-0.5 rounded-full bg-slate-100 border border-slate-200 text-[10px] font-medium text-slate-600">
                    Supabase Unlinked
                  </span>
                )}
              </div>

              <div className="inline-flex items-center gap-2 px-3 py-1 mt-2 rounded-full bg-[#f3eae0] border border-[#d8c8b8] text-[11px] font-semibold text-[#581825]">
                <span>🎯 Goal: {user?.goal?.replace("_", " ")}</span>
                <span>•</span>
                <span>🔥 {user?.daily_calorie_target} kcal</span>
              </div>
            </div>

            {errorMessage && (
              <div className="p-2.5 rounded-xl bg-red-50 border border-red-200 text-red-700 text-xs text-left">
                {errorMessage}
              </div>
            )}

            {linkSuccessMessage && (
              <div className="p-2.5 rounded-xl bg-emerald-50 border border-emerald-200 text-emerald-700 text-xs text-left">
                {linkSuccessMessage}
              </div>
            )}

            {/* Supabase Account Linking / Unlinking */}
            <div className="p-3.5 rounded-2xl bg-white/70 border border-[#e2d6c9] text-left space-y-2.5">
              <div className="flex items-center justify-between">
                <div>
                  <h4 className="text-xs font-bold text-slate-800">Supabase Cloud Sync</h4>
                  <p className="text-[11px] text-slate-500">Sync meal plans across devices with Supabase Auth</p>
                </div>
                {hasSupabase ? (
                  <button
                    onClick={handleUnlinkSupabase}
                    className="px-2.5 py-1 rounded-lg border border-red-200 text-red-600 hover:bg-red-50 text-[10px] font-medium transition"
                  >
                    Unlink
                  </button>
                ) : (
                  <button
                    onClick={() => setIsLinking(!isLinking)}
                    className="px-2.5 py-1 rounded-lg bg-[#1d4ed8] text-white hover:bg-[#1e40af] text-[10px] font-semibold transition"
                  >
                    {isLinking ? "Cancel" : "Link Account"}
                  </button>
                )}
              </div>

              {isLinking && !hasSupabase && (
                <form onSubmit={handleLinkSupabase} className="pt-2 border-t border-slate-200 space-y-2">
                  <input
                    type="email"
                    required
                    placeholder="Supabase account email"
                    value={linkEmail}
                    onChange={(e) => setLinkEmail(e.target.value)}
                    className="w-full px-2.5 py-1.5 rounded-lg bg-white border border-[#d8c8b8] text-xs"
                  />
                  <input
                    type="password"
                    required
                    placeholder="Supabase password"
                    value={linkPassword}
                    onChange={(e) => setLinkPassword(e.target.value)}
                    className="w-full px-2.5 py-1.5 rounded-lg bg-white border border-[#d8c8b8] text-xs"
                  />
                  <button
                    type="submit"
                    className="w-full py-1.5 rounded-lg bg-[#581825] text-white text-xs font-semibold hover:bg-[#421018]"
                  >
                    Verify & Link
                  </button>
                </form>
              )}
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

            {/* Provider Toggle Tabs */}
            <div className="flex rounded-xl bg-[#ede4d8] p-1 text-xs font-semibold text-slate-700">
              <button
                type="button"
                onClick={() => setProviderMode("local")}
                className={`flex-1 py-1.5 rounded-lg transition-all ${
                  providerMode === "local"
                    ? "bg-white text-slate-900 shadow-sm font-bold"
                    : "text-slate-500 hover:text-slate-800"
                }`}
              >
                🔒 Local (Offline)
              </button>
              <button
                type="button"
                onClick={() => setProviderMode("supabase")}
                className={`flex-1 py-1.5 rounded-lg transition-all ${
                  providerMode === "supabase"
                    ? "bg-[#1d4ed8] text-white shadow-sm font-bold"
                    : "text-slate-500 hover:text-slate-800"
                }`}
              >
                ⚡ Supabase Auth
              </button>
            </div>

            {errorMessage && (
              <div className="p-3 rounded-xl bg-red-50 border border-red-200 text-red-700 text-xs">
                {errorMessage}
              </div>
            )}

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
              className={`w-full py-2.5 rounded-xl text-white text-xs font-semibold shadow-md transition-all mt-2 ${
                providerMode === "supabase"
                  ? "bg-[#1d4ed8] hover:bg-[#1e40af]"
                  : "bg-[#581825] hover:bg-[#421018]"
              }`}
            >
              {isRegisterMode
                ? `Register with ${providerMode === "supabase" ? "Supabase" : "Local Account"}`
                : `Sign In with ${providerMode === "supabase" ? "Supabase" : "Local Account"}`}
            </button>

            <div className="text-center pt-2">
              <button
                type="button"
                onClick={() => {
                  setIsRegisterMode(!isRegisterMode);
                  setErrorMessage("");
                }}
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
