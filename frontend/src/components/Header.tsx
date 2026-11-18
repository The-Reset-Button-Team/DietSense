"use client";

import React, { useState } from "react";
import Image from "next/image";
import { GoalType } from "@/types";
import { useAuth } from "@/context/AuthContext";
import { useSync } from "@/context/SyncContext";

interface HeaderProps {
  goal: GoalType;
  targetCalories: number;
  onOpenAuth: () => void;
}

export const Header: React.FC<HeaderProps> = ({ goal, targetCalories, onOpenAuth }) => {
  const { user, isAuthenticated } = useAuth();
  const { syncState, isSyncing, triggerSync } = useSync();
  const isOnline = syncState.status !== "offline";
  const pendingCount = syncState.pending_count;
  const lastSynced = syncState.last_synced_at;
  const syncNow = triggerSync;
  const [syncPopoverOpen, setSyncPopoverOpen] = useState(false);

  const goalText =
    goal === "lose_weight"
      ? "Cut (-400 kcal)"
      : goal === "gain_weight"
      ? "Surplus (+300 kcal)"
      : "Maintain (TDEE)";

  return (
    <header className="sticky top-0 w-full z-40 bg-surface/90 backdrop-blur-xl border-b border-surface-container-highest shadow-[0_1px_8px_rgba(0,0,0,0.04)]">
      <div className="max-w-7xl mx-auto px-margin-mobile md:px-margin-tablet lg:px-margin pt-space-sm pb-space-xs">
        <div className="flex items-center justify-between gap-space-md">
          {/* Brand & Greeting */}
          <div className="flex items-center gap-space-md">
            <a
              href="#"
              className="flex items-center focus:outline-none focus:ring-1 focus:ring-primary rounded py-0.5"
            >
              <div className="relative h-9 w-auto shrink-0 flex items-center">
                <Image
                  src="/images/dietsense-logo.jpg"
                  alt="DietSense"
                  width={145}
                  height={42}
                  className="h-9 w-auto object-contain"
                  priority
                />
              </div>
            </a>

            <div className="hidden sm:flex items-center pl-space-md bg-surface-container-low px-space-md py-1 rounded-full shadow-[0_1px_4px_rgba(0,0,0,0.02)]">
              <span className="font-headline-md text-headline-md italic text-primary font-serif">
                Namaste,&nbsp;
              </span>
              <span className="font-headline-md text-headline-md text-on-surface font-serif">
                {user?.full_name || "Daksh"}
              </span>
            </div>
          </div>

          {/* Right Action Cluster: Goal Pill, Sync Hub Popover, User Avatar */}
          <div className="flex items-center gap-space-sm md:gap-space-md">
            {/* Clinical Target Pill */}
            <div className="hidden lg:flex items-center gap-space-xs px-space-md py-1 bg-surface-container-lowest rounded-full shadow-[0_1px_4px_rgba(0,0,0,0.03)] border border-surface-container">
              <span className="material-symbols-outlined text-[16px] text-primary">
                local_fire_department
              </span>
              <span className="font-label-md text-label-md text-primary font-bold">
                {goalText}
              </span>
              <span className="text-on-surface-variant font-label-md text-label-md">•</span>
              <span className="font-metric-num text-[14px] leading-5 text-on-surface">
                {targetCalories.toLocaleString()} kcal/day
              </span>
            </div>

            {/* Database Sync Hub Popover */}
            <div className="relative">
              <button
                type="button"
                aria-label="Database sync status"
                onClick={() => setSyncPopoverOpen(!syncPopoverOpen)}
                className="flex items-center gap-space-xs px-space-sm md:px-space-md py-1 bg-surface-container-low hover:bg-surface-container-high hover:text-on-surface rounded-full transition-all focus:outline-none focus:ring-1 focus:ring-primary border border-surface-container text-on-surface"
              >
                <span
                  className={`w-2 h-2 rounded-full ring-2 ${
                    isSyncing
                      ? "bg-amber-500 ring-amber-500/20 animate-spin"
                      : isOnline
                      ? "bg-secondary ring-secondary/20 animate-pulse"
                      : "bg-surface-dim ring-surface-dim/20"
                  }`}
                />
                <span className="font-label-md text-label-md text-secondary font-semibold hidden sm:inline">
                  {isSyncing ? "Syncing..." : isOnline ? "Synced" : "Offline"}
                </span>
                <span className="material-symbols-outlined text-[16px] text-on-surface-variant">
                  keyboard_arrow_down
                </span>
              </button>

              {syncPopoverOpen && (
                <div className="absolute right-0 mt-2 w-72 p-space-md bg-surface-container-lowest rounded-xl shadow-[0_8px_24px_-4px_rgba(66,16,24,0.08),0_2px_6px_-1px_rgba(66,16,24,0.04)] border border-surface-container z-50 animate-in fade-in zoom-in-95 duration-150">
                  <div className="flex items-center justify-between pb-space-xs mb-space-sm border-b border-surface-container">
                    <span className="font-label-lg text-label-lg text-on-surface font-semibold">
                      Database Sync Hub
                    </span>
                    <span className="font-label-sm text-label-sm text-secondary bg-secondary-container/40 px-2 py-0.5 rounded-full">
                      {isOnline ? "Live" : "Standby"}
                    </span>
                  </div>

                  <div className="space-y-2 mb-space-md text-body-sm font-body-sm">
                    <div className="flex items-center justify-between">
                      <span className="flex items-center gap-space-xs text-on-surface">
                        <span className="w-2 h-2 rounded-full bg-secondary" />
                        Local SQLite
                      </span>
                      <span className="font-label-sm text-label-sm text-on-surface-variant">
                        v4.1.2 • Optimal
                      </span>
                    </div>

                    <div className="flex items-center justify-between">
                      <span className="flex items-center gap-space-xs text-on-surface">
                        <span className="w-2 h-2 rounded-full bg-secondary" />
                        Supabase Cloud
                      </span>
                      <span className="font-label-sm text-label-sm text-on-surface-variant">
                        {lastSynced ? "Just now" : "Ready"}
                      </span>
                    </div>

                    <div className="flex items-center justify-between opacity-70">
                      <span className="flex items-center gap-space-xs text-on-surface">
                        <span className="w-2 h-2 rounded-full bg-surface-dim" />
                        Offline Queue
                      </span>
                      <span className="font-label-sm text-label-sm text-on-surface-variant">
                        {pendingCount} pending
                      </span>
                    </div>
                  </div>

                  <button
                    type="button"
                    onClick={async () => {
                      await syncNow();
                    }}
                    disabled={isSyncing}
                    className="w-full py-1.5 px-space-md bg-primary hover:bg-primary-container text-on-primary hover:text-on-primary-container rounded font-label-md text-label-md transition-colors flex items-center justify-center gap-space-xs disabled:opacity-50"
                  >
                    <span className="material-symbols-outlined text-[16px]">sync</span>
                    {isSyncing ? "Syncing..." : "Force Ledger Re-sync"}
                  </button>
                </div>
              )}
            </div>

            {/* Profile Avatar Capsule */}
            <button
              type="button"
              onClick={onOpenAuth}
              aria-label="User Account"
              className="flex items-center pl-space-xs rounded-full hover:ring-2 hover:ring-primary/20 transition-all focus:outline-none"
            >
              <div className="relative w-8 h-8 rounded-full overflow-hidden ring-1 ring-outline-variant/60">
                <Image
                  src="/stitch/assets/stitch_asset_10.png"
                  alt="Profile"
                  width={32}
                  height={32}
                  className="w-8 h-8 rounded-full object-cover"
                />
              </div>
            </button>
          </div>
        </div>
      </div>
    </header>
  );
};
