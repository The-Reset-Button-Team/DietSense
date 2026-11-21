"use client";

import React from "react";

export type TabType = "today" | "pantry" | "foods" | "progress" | "profile" | "swap" | "safety" | "ai";

interface TabNavProps {
  activeTab: TabType;
  setActiveTab: (tab: TabType) => void;
}

export const TabNav: React.FC<TabNavProps> = ({ activeTab, setActiveTab }) => {
  const primaryTabs: { id: TabType; label: string; icon: string }[] = [
    { id: "today", label: "Today's Plan", icon: "calendar_today" },
    { id: "pantry", label: "AI Pantry & Scanner", icon: "inventory_2" },
    { id: "foods", label: "Food Catalog", icon: "restaurant_menu" },
    { id: "progress", label: "Progress & Analytics", icon: "monitoring" },
    { id: "profile", label: "Profile Studio", icon: "tune" },
  ];

  const extendedTabs: { id: TabType; label: string; icon: string }[] = [
    { id: "swap", label: "Mindful Swap", icon: "swap_horiz" },
    { id: "safety", label: "Safety Shield", icon: "shield" },
    { id: "ai", label: "AI Meal Coach", icon: "smart_toy" },
  ];

  return (
    <div className="w-full bg-surface/70 border-b border-surface-container-highest">
      <div className="max-w-7xl mx-auto px-margin-mobile md:px-margin-tablet lg:px-margin">
        <nav
          className="flex items-center gap-space-xs sm:gap-space-sm overflow-x-auto py-2 scrollbar-none"
          aria-label="Main Navigation"
        >
          {primaryTabs.map((tab) => {
            const isActive = activeTab === tab.id;
            return (
              <button
                key={tab.id}
                type="button"
                onClick={() => setActiveTab(tab.id)}
                className={`font-label-lg text-label-lg px-space-md py-1.5 transition-all whitespace-nowrap flex items-center gap-1.5 ${
                  isActive
                    ? "bg-primary-container text-on-primary font-semibold rounded shadow-[0_1px_4px_rgba(88,24,37,0.1)]"
                    : "text-on-surface-variant hover:text-on-surface hover:bg-surface-container rounded"
                }`}
              >
                <span className="material-symbols-outlined text-[16px]">{tab.icon}</span>
                <span>{tab.label}</span>
              </button>
            );
          })}

          <div className="h-5 w-px bg-surface-container-highest mx-1 hidden sm:block" />

          {extendedTabs.map((tab) => {
            const isActive = activeTab === tab.id;
            return (
              <button
                key={tab.id}
                type="button"
                onClick={() => setActiveTab(tab.id)}
                className={`font-label-lg text-label-lg px-space-md py-1.5 transition-all whitespace-nowrap flex items-center gap-1.5 ${
                  isActive
                    ? "bg-primary-container text-on-primary font-semibold rounded shadow-[0_1px_4px_rgba(88,24,37,0.1)]"
                    : "text-on-surface-variant hover:text-on-surface hover:bg-surface-container rounded opacity-90"
                }`}
              >
                <span className="material-symbols-outlined text-[16px]">{tab.icon}</span>
                <span>{tab.label}</span>
              </button>
            );
          })}
        </nav>
      </div>
    </div>
  );
};
