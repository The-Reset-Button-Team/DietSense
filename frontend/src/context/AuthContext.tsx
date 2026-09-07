"use client";

import React, { createContext, useContext, useState, useEffect } from "react";
import { User, GoalType, Gender, ActivityLevel } from "@/types";

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

interface AuthContextType {
  user: UserProfileData | null;
  isAuthenticated: boolean;
  login: (email: string, pass: string) => Promise<boolean>;
  register: (data: Partial<UserProfileData>) => Promise<boolean>;
  logout: () => void;
  updateProfile: (updated: Partial<UserProfileData>) => void;
}

const DEFAULT_USER: UserProfileData = {
  id: "usr_99a8b7c6-d5e4-4f3a-2b1c-001122334455",
  email: "arvykrane@dietsense.ai",
  full_name: "arvykrane",
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

export const AuthProvider: React.FC<{ children: React.ReactNode }> = ({ children }) => {
  const [user, setUser] = useState<UserProfileData | null>(null);

  useEffect(() => {
    const saved = localStorage.getItem("dietsense_session");
    if (saved) {
      try {
        setUser(JSON.parse(saved));
      } catch {
        setUser(DEFAULT_USER);
      }
    } else {
      setUser(DEFAULT_USER);
      localStorage.setItem("dietsense_session", JSON.stringify(DEFAULT_USER));
    }
  }, []);

  const login = async (email: string, pass: string): Promise<boolean> => {
    // Instant responsive auth with persistent storage
    const loggedUser: UserProfileData = {
      ...DEFAULT_USER,
      email,
      full_name: email.split("@")[0],
    };
    setUser(loggedUser);
    localStorage.setItem("dietsense_session", JSON.stringify(loggedUser));
    return true;
  };

  const register = async (data: Partial<UserProfileData>): Promise<boolean> => {
    const newUser: UserProfileData = {
      ...DEFAULT_USER,
      ...data,
      id: "usr_" + Date.now(),
    };
    setUser(newUser);
    localStorage.setItem("dietsense_session", JSON.stringify(newUser));
    return true;
  };

  const logout = () => {
    setUser(null);
    localStorage.removeItem("dietsense_session");
  };

  const updateProfile = (updated: Partial<UserProfileData>) => {
    setUser((prev) => {
      if (!prev) return null;
      const next = { ...prev, ...updated };
      localStorage.setItem("dietsense_session", JSON.stringify(next));
      return next;
    });
  };

  return (
    <AuthContext.Provider
      value={{
        user,
        isAuthenticated: !!user,
        login,
        register,
        logout,
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
