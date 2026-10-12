"use client";

import React, { useState, useEffect } from "react";
import Link from "next/link";
import { useRouter, useSearchParams } from "next/navigation";
import { useAuth } from "@/context/AuthContext";

export default function LoginPage() {
  const router = useRouter();
  const searchParams = useSearchParams();
  const nextUrl = searchParams.get("next") || "/";

  const { login, resetPassword, isAuthenticated, isLoading: authLoading } = useAuth();

  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [errorMessage, setErrorMessage] = useState("");
  const [fieldErrors, setFieldErrors] = useState<{ email?: string; password?: string }>({});

  // Forgot password state
  const [isForgotPassword, setIsForgotPassword] = useState(false);
  const [resetSent, setResetSent] = useState(false);
  const [resetLoading, setResetLoading] = useState(false);

  useEffect(() => {
    if (isAuthenticated && !authLoading) {
      router.push(nextUrl);
    }
  }, [isAuthenticated, authLoading, router, nextUrl]);

  const validate = () => {
    const errors: { email?: string; password?: string } = {};
    const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;

    if (!email.trim()) {
      errors.email = "Email address is required.";
    } else if (!emailRegex.test(email.trim())) {
      errors.email = "Please enter a valid email address.";
    }

    if (!password) {
      errors.password = "Password is required.";
    } else if (password.length < 8) {
      errors.password = "Password must be at least 8 characters.";
    }

    setFieldErrors(errors);
    return Object.keys(errors).length === 0;
  };

  const handleLogin = async (e: React.FormEvent) => {
    e.preventDefault();
    setErrorMessage("");

    if (!validate()) return;

    setIsSubmitting(true);
    const result = await login(email, password);
    setIsSubmitting(false);

    if (result.success) {
      router.push(nextUrl);
    } else {
      setErrorMessage(result.error || "Failed to sign in. Please try again.");
    }
  };

  const handleForgotPassword = async (e: React.FormEvent) => {
    e.preventDefault();
    setErrorMessage("");

    const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
    if (!email.trim() || !emailRegex.test(email.trim())) {
      setFieldErrors({ email: "Please enter a valid email address for reset." });
      return;
    }

    setResetLoading(true);
    const result = await resetPassword(email);
    setResetLoading(false);

    if (result.success) {
      setResetSent(true);
    } else {
      setErrorMessage(result.error || "Unable to send password reset email.");
    }
  };

  return (
    <div className="min-h-screen bg-[#fcf9f5] flex items-center justify-center p-4 sm:p-6 text-slate-800">
      <div className="w-full max-w-md bg-white border border-[#e8ded3] rounded-3xl p-6 sm:p-8 shadow-xl relative overflow-hidden">
        {/* Ambient background blur */}
        <div className="absolute -top-16 -right-16 w-44 h-44 bg-[#fed7aa] rounded-full blur-3xl opacity-30 pointer-events-none" />
        <div className="absolute -bottom-16 -left-16 w-44 h-44 bg-[#fbcfe8] rounded-full blur-3xl opacity-30 pointer-events-none" />

        <div className="relative z-10">
          {/* Header */}
          <div className="text-center mb-6">
            <Link href="/" className="inline-block">
              <span className="text-xs font-bold uppercase tracking-wider text-[#581825] bg-[#f3eae0] px-3 py-1 rounded-full border border-[#d8c8b8]">
                DietSense
              </span>
            </Link>
            <h1 className="text-2xl sm:text-3xl font-serif font-bold text-[#421018] mt-3">
              {isForgotPassword ? "Reset Password" : "Sign In to DietSense"}
            </h1>
            <p className="text-xs text-slate-600 mt-1">
              {isForgotPassword
                ? "Enter your account email to receive a password recovery link."
                : "Welcome back! Access your adaptive meal plans and verified nutrition."}
            </p>
          </div>

          {/* Error Banner */}
          {errorMessage && (
            <div
              role="alert"
              className="mb-4 p-3 rounded-xl bg-red-50 border border-red-200 text-xs text-red-700 flex items-start gap-2"
            >
              <span className="text-sm font-bold">⚠️</span>
              <span>{errorMessage}</span>
            </div>
          )}

          {isForgotPassword ? (
            resetSent ? (
              <div className="text-center py-4 space-y-4">
                <div className="w-12 h-12 bg-emerald-50 border border-emerald-200 text-emerald-700 rounded-full flex items-center justify-center mx-auto text-xl">
                  ✉️
                </div>
                <div>
                  <h3 className="text-sm font-bold text-slate-800">Check Your Inbox</h3>
                  <p className="text-xs text-slate-600 mt-1">
                    We sent a password reset link to <strong className="font-mono">{email}</strong>.
                  </p>
                </div>
                <button
                  type="button"
                  onClick={() => {
                    setIsForgotPassword(false);
                    setResetSent(false);
                  }}
                  className="w-full py-2.5 rounded-xl bg-[#581825] text-white text-xs font-semibold hover:bg-[#421018] transition-all"
                >
                  Back to Sign In
                </button>
              </div>
            ) : (
              <form onSubmit={handleForgotPassword} className="space-y-4">
                <div>
                  <label htmlFor="reset-email" className="block text-xs font-semibold text-slate-700 mb-1">
                    Email Address
                  </label>
                  <input
                    id="reset-email"
                    type="email"
                    value={email}
                    onChange={(e) => {
                      setEmail(e.target.value);
                      if (fieldErrors.email) setFieldErrors({ ...fieldErrors, email: undefined });
                    }}
                    placeholder="you@example.com"
                    aria-invalid={!!fieldErrors.email}
                    className={`w-full px-3.5 py-2.5 rounded-xl bg-white border text-xs text-slate-800 transition-all focus:outline-none focus:ring-2 focus:ring-[#1d4ed8] ${
                      fieldErrors.email ? "border-red-400 bg-red-50/20" : "border-[#d8c8b8]"
                    }`}
                  />
                  {fieldErrors.email && (
                    <p className="text-[11px] text-red-600 mt-1">{fieldErrors.email}</p>
                  )}
                </div>

                <button
                  type="submit"
                  disabled={resetLoading}
                  className="w-full py-2.5 rounded-xl bg-[#581825] text-white text-xs font-semibold hover:bg-[#421018] transition-all disabled:opacity-60 flex items-center justify-center gap-2"
                >
                  {resetLoading ? (
                    <>
                      <span className="w-3.5 h-3.5 border-2 border-white border-t-transparent rounded-full animate-spin" />
                      <span>Sending Link...</span>
                    </>
                  ) : (
                    "Send Reset Link"
                  )}
                </button>

                <div className="text-center pt-2">
                  <button
                    type="button"
                    onClick={() => setIsForgotPassword(false)}
                    className="text-xs text-[#1d4ed8] hover:underline font-medium"
                  >
                    Back to Sign In
                  </button>
                </div>
              </form>
            )
          ) : (
            <form onSubmit={handleLogin} className="space-y-4">
              <div>
                <label htmlFor="login-email" className="block text-xs font-semibold text-slate-700 mb-1">
                  Email Address
                </label>
                <input
                  id="login-email"
                  type="email"
                  autoComplete="email"
                  value={email}
                  onChange={(e) => {
                    setEmail(e.target.value);
                    if (fieldErrors.email) setFieldErrors({ ...fieldErrors, email: undefined });
                  }}
                  placeholder="you@example.com"
                  aria-invalid={!!fieldErrors.email}
                  className={`w-full px-3.5 py-2.5 rounded-xl bg-white border text-xs text-slate-800 transition-all focus:outline-none focus:ring-2 focus:ring-[#1d4ed8] ${
                    fieldErrors.email ? "border-red-400 bg-red-50/20" : "border-[#d8c8b8]"
                  }`}
                />
                {fieldErrors.email && (
                  <p className="text-[11px] text-red-600 mt-1">{fieldErrors.email}</p>
                )}
              </div>

              <div>
                <div className="flex items-center justify-between mb-1">
                  <label htmlFor="login-password" className="block text-xs font-semibold text-slate-700">
                    Password
                  </label>
                  <button
                    type="button"
                    onClick={() => {
                      setIsForgotPassword(true);
                      setErrorMessage("");
                    }}
                    className="text-[11px] text-[#1d4ed8] hover:underline font-medium"
                  >
                    Forgot password?
                  </button>
                </div>
                <input
                  id="login-password"
                  type="password"
                  autoComplete="current-password"
                  value={password}
                  onChange={(e) => {
                    setPassword(e.target.value);
                    if (fieldErrors.password) setFieldErrors({ ...fieldErrors, password: undefined });
                  }}
                  placeholder="••••••••"
                  aria-invalid={!!fieldErrors.password}
                  className={`w-full px-3.5 py-2.5 rounded-xl bg-white border text-xs text-slate-800 transition-all focus:outline-none focus:ring-2 focus:ring-[#1d4ed8] ${
                    fieldErrors.password ? "border-red-400 bg-red-50/20" : "border-[#d8c8b8]"
                  }`}
                />
                {fieldErrors.password && (
                  <p className="text-[11px] text-red-600 mt-1">{fieldErrors.password}</p>
                )}
              </div>

              <button
                type="submit"
                disabled={isSubmitting}
                className="w-full py-2.5 rounded-xl bg-[#581825] text-white text-xs font-semibold hover:bg-[#421018] shadow-md transition-all disabled:opacity-60 flex items-center justify-center gap-2 mt-2"
              >
                {isSubmitting ? (
                  <>
                    <span className="w-3.5 h-3.5 border-2 border-white border-t-transparent rounded-full animate-spin" />
                    <span>Signing In...</span>
                  </>
                ) : (
                  "Sign In"
                )}
              </button>

              <div className="text-center pt-3 border-t border-[#e8ded3]">
                <p className="text-xs text-slate-600">
                  Don&apos;t have an account yet?{" "}
                  <Link
                    href={`/signup${nextUrl !== "/" ? `?next=${encodeURIComponent(nextUrl)}` : ""}`}
                    className="text-[#1d4ed8] font-semibold hover:underline"
                  >
                    Create Account
                  </Link>
                </p>
              </div>
            </form>
          )}
        </div>
      </div>
    </div>
  );
}
