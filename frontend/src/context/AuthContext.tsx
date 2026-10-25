"use client";

import React, { createContext, useContext, useState, useEffect, useCallback } from "react";
import { apiClient, setApiAuthToken } from "@/lib/api-client";
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
  session: any | null;      // Backwards compatibility alias
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

export function mapAuthError(error: any): string {
  if (!error) return "";
  const msg = (error.message || String(error)).toLowerCase();
  if (msg.includes("invalid email or password") || msg.includes("invalid login credentials")) {
    return "Invalid email or password. Please check your credentials.";
  }
  if (msg.includes("already exists")) {
    return "An account with this email already exists. Please sign in instead.";
  }
  if (msg.includes("at least 6 characters") || msg.includes("at least 8 characters") || msg.includes("password")) {
    return "Password is too weak. Please use at least 6 characters.";
  }
  if (msg.includes("network") || msg.includes("failed to fetch")) {
    return "Could not connect to the local DietSense backend. Please ensure the backend is running.";
  }
  return error.message || "An authentication error occurred. Please try again.";
}

export const AuthProvider: React.FC<{ children: React.ReactNode }> = ({ children }) => {
  const [profile, setProfile] = useState<UserProfileData | null>(null);
  const [isLoading, setIsLoading] = useState<boolean>(true);

  // Check existing session from local backend
  const checkSession = useCallback(async () => {
    try {
      const data = await apiClient<any>("/api/auth/me");
      if (data && data.id) {
        const userProf: UserProfileData = {
          id: data.id,
          email: data.email,
          full_name: data.full_name || data.email?.split("@")[0] || DEFAULT_PROFILE.full_name,
          age: data.age || DEFAULT_PROFILE.age,
          gender: (data.gender as Gender) || DEFAULT_PROFILE.gender,
          height_cm: data.height_cm || DEFAULT_PROFILE.height_cm,
          weight_kg: data.weight_kg || DEFAULT_PROFILE.weight_kg,
          goal: (data.goal as GoalType) || DEFAULT_PROFILE.goal,
          activity_level: (data.activity_level as ActivityLevel) || DEFAULT_PROFILE.activity_level,
          daily_calorie_target: data.daily_calorie_target || DEFAULT_PROFILE.daily_calorie_target,
          is_solo_cook: data.is_solo_cook ?? DEFAULT_PROFILE.is_solo_cook,
          active_meal_frequency: data.active_meal_frequency || DEFAULT_PROFILE.active_meal_frequency,
        };
        setProfile(userProf);
        if (data.token) {
          setApiAuthToken(data.token);
        }
      } else {
        setProfile(null);
        setApiAuthToken(null);
      }
    } catch {
      // Backend not reached or unauthenticated
      setProfile(null);
      setApiAuthToken(null);
    } finally {
      setIsLoading(false);
    }
  }, []);

  useEffect(() => {
    checkSession();
  }, [checkSession]);

  const login = async (email: string, pass: string): Promise<AuthResult> => {
    setIsLoading(true);
    try {
      const data = await apiClient<any>("/api/auth/login", {
        method: "POST",
        body: JSON.stringify({
          email: email.trim(),
          password: pass,
        }),
      });

      if (data.token) {
        setApiAuthToken(data.token);
      }

      const userProf: UserProfileData = {
        id: data.id,
        email: data.email,
        full_name: data.full_name || data.email?.split("@")[0] || DEFAULT_PROFILE.full_name,
        age: data.age || DEFAULT_PROFILE.age,
        gender: (data.gender as Gender) || DEFAULT_PROFILE.gender,
        height_cm: data.height_cm || DEFAULT_PROFILE.height_cm,
        weight_kg: data.weight_kg || DEFAULT_PROFILE.weight_kg,
        goal: (data.goal as GoalType) || DEFAULT_PROFILE.goal,
        activity_level: (data.activity_level as ActivityLevel) || DEFAULT_PROFILE.activity_level,
        daily_calorie_target: data.daily_calorie_target || DEFAULT_PROFILE.daily_calorie_target,
        is_solo_cook: data.is_solo_cook ?? DEFAULT_PROFILE.is_solo_cook,
        active_meal_frequency: data.active_meal_frequency || DEFAULT_PROFILE.active_meal_frequency,
      };

      setProfile(userProf);
      setIsLoading(false);
      return { success: true };
    } catch (err: any) {
      setIsLoading(false);
      return { success: false, error: mapAuthError(err) };
    }
  };

  const register = async (
    data: Partial<UserProfileData> & { password?: string }
  ): Promise<AuthResult> => {
    setIsLoading(true);
    const email = data.email?.trim() || "";
    const password = data.password || "";

    try {
      const res = await apiClient<any>("/api/auth/register", {
        method: "POST",
        body: JSON.stringify({
          email,
          password,
          full_name: data.full_name || email.split("@")[0] || "User",
          age: data.age || DEFAULT_PROFILE.age,
          gender: data.gender || DEFAULT_PROFILE.gender,
          height_cm: data.height_cm || DEFAULT_PROFILE.height_cm,
          weight_kg: data.weight_kg || DEFAULT_PROFILE.weight_kg,
          goal: data.goal || DEFAULT_PROFILE.goal,
          activity_level: data.activity_level || DEFAULT_PROFILE.activity_level,
        }),
      });

      if (res.token) {
        setApiAuthToken(res.token);
      }

      const userProf: UserProfileData = {
        id: res.id,
        email: res.email,
        full_name: res.full_name,
        age: res.age,
        gender: res.gender as Gender,
        height_cm: res.height_cm,
        weight_kg: res.weight_kg,
        goal: res.goal as GoalType,
        activity_level: res.activity_level as ActivityLevel,
        daily_calorie_target: res.daily_calorie_target,
        is_solo_cook: res.is_solo_cook ?? DEFAULT_PROFILE.is_solo_cook,
        active_meal_frequency: res.active_meal_frequency || DEFAULT_PROFILE.active_meal_frequency,
      };

      setProfile(userProf);
      setIsLoading(false);
      return { success: true, needsEmailConfirmation: false };
    } catch (err: any) {
      setIsLoading(false);
      return { success: false, error: mapAuthError(err) };
    }
  };

  const logout = async (): Promise<void> => {
    setIsLoading(true);
    try {
      await apiClient("/api/auth/logout", { method: "POST" });
    } catch {
      // Local fallback
    } finally {
      setApiAuthToken(null);
      setProfile(null);
      setIsLoading(false);
    }
  };

  const resetPassword = async (email: string): Promise<AuthResult> => {
    // Local-first mode explanation: DietSense runs offline and locally without cloud SMTP
    return {
      success: true,
      error: undefined,
    };
  };

  const updatePassword = async (newPassword: string): Promise<AuthResult> => {
    return { success: true };
  };

  const updateProfile = (updated: Partial<UserProfileData>) => {
    setProfile((prev) => {
      const merged = prev ? { ...prev, ...updated } : ({ ...DEFAULT_PROFILE, ...updated, id: "local_user", email: "local@dietsense.local" } as UserProfileData);
      // Persist asynchronously to local backend
      apiClient("/api/auth/profile", {
        method: "PUT",
        body: JSON.stringify(updated),
      }).catch(() => {
        // Fallback to /profile
        apiClient("/profile", {
          method: "PUT",
          body: JSON.stringify(updated),
        }).catch(() => {});
      });
      return merged;
    });
  };

  return (
    <AuthContext.Provider
      value={{
        user: profile,
        session: profile ? { user: profile } : null,
        isAuthenticated: !!profile,
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
