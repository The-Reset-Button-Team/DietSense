"use client";

import React, { createContext, useContext, useState, useEffect, useCallback } from "react";
import { User, Session, AuthError } from "@supabase/supabase-js";
import { createClient } from "@/lib/supabaseClient";
import { GoalType, Gender, ActivityLevel } from "@/types";

export interface UserProfileData {
  id: string;
  email: string;
  full_name: string;
  age: number;
  gender: Gender;
  height_cm: number;
  weight_kg: number;
  goal: GoalType;
  activity_level: ActivityLevel;
  daily_calorie_target: number;
  is_solo_cook: boolean;
  active_meal_frequency: string;
}

export interface AuthResult {
  success: boolean;
  needsEmailConfirmation?: boolean;
  error?: string;
}

interface AuthContextType {
  user: UserProfileData | null;
  supabaseUser: User | null;
  session: Session | null;
  isAuthenticated: boolean;
  isLoading: boolean;
  login: (email: string, pass: string) => Promise<AuthResult>;
  register: (data: Partial<UserProfileData> & { password?: string }) => Promise<AuthResult>;
  logout: () => Promise<void>;
  resetPassword: (email: string) => Promise<AuthResult>;
  updatePassword: (newPassword: string) => Promise<AuthResult>;
  updateProfile: (updated: Partial<UserProfileData>) => void;
}

const DEFAULT_PROFILE: Omit<UserProfileData, "id" | "email"> = {
  full_name: "User",
  age: 26,
  gender: "male",
  height_cm: 175,
  weight_kg: 75,
  goal: "lose_weight",
  activity_level: "lightly_active",
  daily_calorie_target: 1850,
  is_solo_cook: true,
  active_meal_frequency: "3_meals",
};

const AuthContext = createContext<AuthContextType | undefined>(undefined);

export function mapSupabaseAuthError(error: AuthError | Error | null): string {
  if (!error) return "";
  const msg = error.message.toLowerCase();
  if (msg.includes("invalid login credentials") || msg.includes("invalid credentials")) {
    return "Invalid email or password. Please check your credentials.";
  }
  if (msg.includes("user already registered") || msg.includes("already registered")) {
    return "An account with this email already exists. Please sign in instead.";
  }
  if (msg.includes("password should be at least") || msg.includes("weak password")) {
    return "Password is too weak. Please use at least 8 characters.";
  }
  if (msg.includes("email not confirmed")) {
    return "Please confirm your email address before signing in. Check your inbox.";
  }
  if (msg.includes("rate limit") || msg.includes("too many requests")) {
    return "Too many attempts. Please wait a few moments and try again.";
  }
  return error.message || "An authentication error occurred. Please try again.";
}

export const AuthProvider: React.FC<{ children: React.ReactNode }> = ({ children }) => {
  const [supabaseUser, setSupabaseUser] = useState<User | null>(null);
  const [session, setSession] = useState<Session | null>(null);
  const [profile, setProfile] = useState<UserProfileData | null>(null);
  const [isLoading, setIsLoading] = useState<boolean>(true);

  const supabase = createClient();

  const syncUserFromSession = useCallback((currentSession: Session | null) => {
    if (currentSession?.user) {
      const u = currentSession.user;
      setSupabaseUser(u);
      setSession(currentSession);

      const meta = u.user_metadata || {};
      const mergedProfile: UserProfileData = {
        id: u.id,
        email: u.email || "",
        full_name: meta.full_name || meta.name || u.email?.split("@")[0] || "User",
        age: meta.age || DEFAULT_PROFILE.age,
        gender: meta.gender || DEFAULT_PROFILE.gender,
        height_cm: meta.height_cm || DEFAULT_PROFILE.height_cm,
        weight_kg: meta.weight_kg || DEFAULT_PROFILE.weight_kg,
        goal: meta.goal || DEFAULT_PROFILE.goal,
        activity_level: meta.activity_level || DEFAULT_PROFILE.activity_level,
        daily_calorie_target: meta.daily_calorie_target || DEFAULT_PROFILE.daily_calorie_target,
        is_solo_cook: meta.is_solo_cook ?? DEFAULT_PROFILE.is_solo_cook,
        active_meal_frequency: meta.active_meal_frequency || DEFAULT_PROFILE.active_meal_frequency,
      };

      setProfile(mergedProfile);
      if (typeof window !== "undefined") {
        localStorage.setItem("dietsense_session", JSON.stringify(mergedProfile));
      }
    } else {
      setSupabaseUser(null);
      setSession(null);
      setProfile(null);
      if (typeof window !== "undefined") {
        localStorage.removeItem("dietsense_session");
      }
    }
    setIsLoading(false);
  }, []);

  useEffect(() => {
    let mounted = true;

    // 1. Initial session check
    supabase.auth.getSession().then(({ data: { session } }) => {
      if (mounted) {
        syncUserFromSession(session);
      }
    }).catch(() => {
      if (mounted) {
        setIsLoading(false);
      }
    });

    // 2. Auth state subscription
    const { data: { subscription } } = supabase.auth.onAuthStateChange(
      (_event, updatedSession) => {
        if (mounted) {
          syncUserFromSession(updatedSession);
        }
      }
    );

    return () => {
      mounted = false;
      subscription?.unsubscribe();
    };
  }, [supabase, syncUserFromSession]);

  const login = async (email: string, pass: string): Promise<AuthResult> => {
    setIsLoading(true);
    try {
      const { data, error } = await supabase.auth.signInWithPassword({
        email: email.trim(),
        password: pass,
      });

      if (error) {
        setIsLoading(false);
        return { success: false, error: mapSupabaseAuthError(error) };
      }

      syncUserFromSession(data.session);
      return { success: true };
    } catch (err: any) {
      setIsLoading(false);
      return { success: false, error: mapSupabaseAuthError(err) };
    }
  };

  const register = async (
    data: Partial<UserProfileData> & { password?: string }
  ): Promise<AuthResult> => {
    setIsLoading(true);
    const email = data.email?.trim() || "";
    const password = data.password || "";

    try {
      const siteUrl = process.env.NEXT_PUBLIC_SITE_URL || (typeof window !== "undefined" ? window.location.origin : "");
      const { data: authData, error } = await supabase.auth.signUp({
        email,
        password,
        options: {
          data: {
            full_name: data.full_name || email.split("@")[0],
            age: data.age || DEFAULT_PROFILE.age,
            gender: data.gender || DEFAULT_PROFILE.gender,
            height_cm: data.height_cm || DEFAULT_PROFILE.height_cm,
            weight_kg: data.weight_kg || DEFAULT_PROFILE.weight_kg,
            goal: data.goal || DEFAULT_PROFILE.goal,
            activity_level: data.activity_level || DEFAULT_PROFILE.activity_level,
            daily_calorie_target: data.daily_calorie_target || DEFAULT_PROFILE.daily_calorie_target,
            is_solo_cook: data.is_solo_cook ?? DEFAULT_PROFILE.is_solo_cook,
            active_meal_frequency: data.active_meal_frequency || DEFAULT_PROFILE.active_meal_frequency,
          },
          emailRedirectTo: siteUrl ? `${siteUrl}/auth/callback` : undefined,
        },
      });

      if (error) {
        setIsLoading(false);
        return { success: false, error: mapSupabaseAuthError(error) };
      }

      // Check if session was returned directly (confirm email OFF) or user needs confirmation (confirm email ON)
      if (authData.session) {
        syncUserFromSession(authData.session);
        return { success: true, needsEmailConfirmation: false };
      } else {
        setIsLoading(false);
        return { success: true, needsEmailConfirmation: true };
      }
    } catch (err: any) {
      setIsLoading(false);
      return { success: false, error: mapSupabaseAuthError(err) };
    }
  };

  const logout = async () => {
    setIsLoading(true);
    try {
      await supabase.auth.signOut();
    } catch {
      // ignore
    } finally {
      syncUserFromSession(null);
    }
  };

  const resetPassword = async (email: string): Promise<AuthResult> => {
    try {
      const siteUrl = process.env.NEXT_PUBLIC_SITE_URL || (typeof window !== "undefined" ? window.location.origin : "");
      const { error } = await supabase.auth.resetPasswordForEmail(email.trim(), {
        redirectTo: siteUrl ? `${siteUrl}/update-password` : undefined,
      });
      if (error) {
        return { success: false, error: mapSupabaseAuthError(error) };
      }
      return { success: true };
    } catch (err: any) {
      return { success: false, error: mapSupabaseAuthError(err) };
    }
  };

  const updatePassword = async (newPassword: string): Promise<AuthResult> => {
    try {
      const { error } = await supabase.auth.updateUser({
        password: newPassword,
      });
      if (error) {
        return { success: false, error: mapSupabaseAuthError(error) };
      }
      return { success: true };
    } catch (err: any) {
      return { success: false, error: mapSupabaseAuthError(err) };
    }
  };

  const updateProfile = (updated: Partial<UserProfileData>) => {
    setProfile((prev) => {
      if (!prev) return null;
      const next = { ...prev, ...updated };
      if (typeof window !== "undefined") {
        localStorage.setItem("dietsense_session", JSON.stringify(next));
      }
      // Also update Supabase metadata in background if possible
      supabase.auth.updateUser({
        data: updated,
      }).catch(() => {});
      return next;
    });
  };

  return (
    <AuthContext.Provider
      value={{
        user: profile,
        supabaseUser,
        session,
        isAuthenticated: !!supabaseUser || !!profile,
        isLoading,
        login,
        register,
        logout,
        resetPassword,
        updatePassword,
        updateProfile,
      }}
    >
      {children}
    </AuthContext.Provider>
  );
};

export const useAuth = () => {
  const context = useContext(AuthContext);
  if (!context) {
    throw new Error("useAuth must be used within an AuthProvider");
  }
  return context;
};
