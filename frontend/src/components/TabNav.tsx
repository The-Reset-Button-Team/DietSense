import React from "react";

export type TabType = "today" | "pantry" | "profile" | "swap" | "safety";

interface TabNavProps {
  activeTab: TabType;
  setActiveTab: (tab: TabType) => void;
}

export const TabNav: React.FC<TabNavProps> = ({ activeTab, setActiveTab }) => {
  const tabs: { id: TabType; icon: string; label: string }[] = [
    { id: "today", icon: "🥣", label: "Daily Meal Plan & Hinglish Recipes" },
    { id: "pantry", icon: "🛒", label: "Grocery AI Scanner & Pantry" },
    { id: "profile", icon: "👤", label: "Routine & Biometrics" },
    { id: "swap", icon: "✨", label: "Mindful Swap" },
    { id: "safety", icon: "🛡️", label: "Safety Shield" },
  ];

  return (
    <div className="relative z-10 flex gap-2 my-5 pb-1 overflow-x-auto text-xs">
      {tabs.map((tab) => {
        const isActive = activeTab === tab.id;
        return (
          <button
            key={tab.id}
            onClick={() => setActiveTab(tab.id)}
            className={`px-4 py-2 rounded-xl border transition-all font-medium flex items-center gap-1.5 shrink-0 ${
              isActive
                ? "bg-[#581825] text-white border-[#581825] shadow-sm"
                : "border-[#d8c8b8] bg-white/80 text-slate-600 hover:text-[#581825]"
            }`}
          >
            <span>{tab.icon}</span> {tab.label}
          </button>
        );
      })}
    </div>
  );
};
