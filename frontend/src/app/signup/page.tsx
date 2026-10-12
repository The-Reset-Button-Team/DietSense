"use client";

import React, { useState, useEffect } from "react";
import Link from "next/link";
import { useRouter, useSearchParams } from "next/navigation";
import { useAuth } from "@/context/AuthContext";

export default function SignupPage() {
  const router = useRouter();
  const searchParams = useSearchParams();
  const nextUrl = searchParams.get("next") || "/";

  const { register, isAuthenticated, isLoading: authLoading } = useAuth();

  const [fullName, setFullName] = useState("");
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [confirmPassword, setConfirmPassword] = useState("");

  const [isSubmitting, setIsSubmitting] = useState(false);
  const [errorMessage, setErrorMessage] = useState("");
  const [fieldErrors, setFieldErrors] = useState<{
    fullName?: string;
    email?: string;
    password?: string;
    confirmPassword?: string;
  }>({});

  const [needsConfirmation, setNeedsConfirmation] = useState(false);

  useEffect(() => {
    if (isAuthenticated && !authLoading) {
      router.push(nextUrl);
    }
  }, [isAuthenticated, authLoading, router, nextUrl]);

  const validate = () => {
    const errors: {
      fullName?: string;
      email?: string;
      password?: string;
      confirmPassword?: string;
    } = {};

    const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;

    if (!fullName.trim()) {
      errors.fullName = "Please enter your full name.";
    }

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

    if (!confirmPassword) {
      errors.confirmPassword = "Please confirm your password.";
    } else if (password !== confirmPassword) {
      errors.confirmPassword = "Passwords do not match.";
    }

    setFieldErrors(errors);
    return Object.keys(errors).length === 0;
  };

  const handleSignup = async (e: React.FormEvent) => {
    e.preventDefault();
    setErrorMessage("");

    if (!validate()) return;

    setIsSubmitting(true);
    const result = await register({
      email,
      password,
      full_name: fullName.trim(),
    });
    setIsSubmitting(false);

    if (result.success) {
      if (result.needsEmailConfirmation) {
        setNeedsConfirmation(true);
      } else {
        router.push(nextUrl);
      }
    } else {
      setErrorMessage(result.error || "Failed to create account. Please try again.");
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
              {needsConfirmation ? "Verify Your Email" : "Create Your Account"}
            </h1>
            <p className="text-xs text-slate-600 mt-1">
              {needsConfirmation
                ? "Your registration is almost complete."
                : "Join DietSense for evidence-based adaptive meal planning."}
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

          {needsConfirmation ? (
            <div className="text-center py-4 space-y-4">
              <div className="w-14 h-14 bg-emerald-50 border border-emerald-200 text-emerald-700 rounded-full flex items-center justify-center mx-auto text-2xl shadow-inner">
                📬
              </div>
              <div>
                <h3 className="text-base font-bold text-slate-800">Check Your Inbox</h3>
                <p className="text-xs text-slate-600 mt-1.5 leading-relaxed">
                  We sent a confirmation link to <strong className="font-mono text-slate-800">{email}</strong>.
                  Please click the link in your email to activate your account.
                </p>
              </div>

              <div className="pt-2">
                <Link
                  href={`/login${nextUrl !== "/" ? `?next=${encodeURIComponent(nextUrl)}` : ""}`}
                  className="block w-full py-2.5 rounded-xl bg-[#581825] text-white text-xs font-semibold hover:bg-[#421018] transition-all text-center"
                >
                  Proceed to Sign In
                </Link>
              </div>
            </div>
          ) : (
            <form onSubmit={handleSignup} className="space-y-3.5">
              <div>
                <label htmlFor="signup-name" className="block text-xs font-semibold text-slate-700 mb-1">
                  Full Name
                </label>
                <input
                  id="signup-name"
                  type="text"
                  autoComplete="name"
                  value={fullName}
                  onChange={(e) => {
                    setFullName(e.target.value);
                    if (fieldErrors.fullName) setFieldErrors({ ...fieldErrors, fullName: undefined });
                  }}
                  placeholder="e.g. Arvy Krane"
                  aria-invalid={!!fieldErrors.fullName}
                  className={`w-full px-3.5 py-2 rounded-xl bg-white border text-xs text-slate-800 transition-all focus:outline-none focus:ring-2 focus:ring-[#1d4ed8] ${
                    fieldErrors.fullName ? "border-red-400 bg-red-50/20" : "border-[#d8c8b8]"
                  }`}
                />
                {fieldErrors.fullName && (
                  <p className="text-[11px] text-red-600 mt-1">{fieldErrors.fullName}</p>
                )}
              </div>

              <div>
                <label htmlFor="signup-email" className="block text-xs font-semibold text-slate-700 mb-1">
                  Email Address
                </label>
                <input
                  id="signup-email"
                  type="email"
                  autoComplete="email"
                  value={email}
                  onChange={(e) => {
                    setEmail(e.target.value);
                    if (fieldErrors.email) setFieldErrors({ ...fieldErrors, email: undefined });
                  }}
                  placeholder="you@example.com"
                  aria-invalid={!!fieldErrors.email}
                  className={`w-full px-3.5 py-2 rounded-xl bg-white border text-xs text-slate-800 transition-all focus:outline-none focus:ring-2 focus:ring-[#1d4ed8] ${
                    fieldErrors.email ? "border-red-400 bg-red-50/20" : "border-[#d8c8b8]"
                  }`}
                />
                {fieldErrors.email && (
                  <p className="text-[11px] text-red-600 mt-1">{fieldErrors.email}</p>
                )}
              </div>

              <div>
                <label htmlFor="signup-password" className="block text-xs font-semibold text-slate-700 mb-1">
                  Password (min. 8 characters)
                </label>
                <input
                  id="signup-password"
                  type="password"
                  autoComplete="new-password"
                  value={password}
                  onChange={(e) => {
                    setPassword(e.target.value);
                    if (fieldErrors.password) setFieldErrors({ ...fieldErrors, password: undefined });
                  }}
                  placeholder="••••••••"
                  aria-invalid={!!fieldErrors.password}
                  className={`w-full px-3.5 py-2 rounded-xl bg-white border text-xs text-slate-800 transition-all focus:outline-none focus:ring-2 focus:ring-[#1d4ed8] ${
                    fieldErrors.password ? "border-red-400 bg-red-50/20" : "border-[#d8c8b8]"
                  }`}
                />
                {fieldErrors.password && (
                  <p className="text-[11px] text-red-600 mt-1">{fieldErrors.password}</p>
                )}
              </div>

              <div>
                <label htmlFor="signup-confirm-password" className="block text-xs font-semibold text-slate-700 mb-1">
                  Confirm Password
                </label>
                <input
                  id="signup-confirm-password"
                  type="password"
                  autoComplete="new-password"
                  value={confirmPassword}
                  onChange={(e) => {
                    setConfirmPassword(e.target.value);
                    if (fieldErrors.confirmPassword) {
                      setFieldErrors({ ...fieldErrors, confirmPassword: undefined });
                    }
                  }}
                  placeholder="••••••••"
                  aria-invalid={!!fieldErrors.confirmPassword}
                  className={`w-full px-3.5 py-2 rounded-xl bg-white border text-xs text-slate-800 transition-all focus:outline-none focus:ring-2 focus:ring-[#1d4ed8] ${
                    fieldErrors.confirmPassword ? "border-red-400 bg-red-50/20" : "border-[#d8c8b8]"
                  }`}
                />
                {fieldErrors.confirmPassword && (
                  <p className="text-[11px] text-red-600 mt-1">{fieldErrors.confirmPassword}</p>
                )}
              </div>

              <button
                type="submit"
                disabled={isSubmitting}
                className="w-full py-2.5 rounded-xl bg-[#581825] text-white text-xs font-semibold hover:bg-[#421018] shadow-md transition-all disabled:opacity-60 flex items-center justify-center gap-2 mt-3"
              >
                {isSubmitting ? (
                  <>
                    <span className="w-3.5 h-3.5 border-2 border-white border-t-transparent rounded-full animate-spin" />
                    <span>Creating Account...</span>
                  </>
                ) : (
                  "Create Account"
                )}
              </button>

              <div className="text-center pt-3 border-t border-[#e8ded3]">
                <p className="text-xs text-slate-600">
                  Already have an account?{" "}
                  <Link
                    href={`/login${nextUrl !== "/" ? `?next=${encodeURIComponent(nextUrl)}` : ""}`}
                    className="text-[#1d4ed8] font-semibold hover:underline"
                  >
                    Sign In
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
