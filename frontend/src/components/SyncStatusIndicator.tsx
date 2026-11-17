"use client";

import React, { useState, useRef, useEffect } from "react";
import { useSync } from "@/context/SyncContext";
import { useAuth } from "@/context/AuthContext";

export const SyncStatusIndicator: React.FC = () => {
  const { isAuthenticated } = useAuth();
  const { syncState, isSyncing, triggerSync, retryFailedSync } = useSync();
  const [isOpen, setIsOpen] = useState(false);
  const popoverRef = useRef<HTMLDivElement>(null);

  // Close dropdown when clicking outside
  useEffect(() => {
    function handleClickOutside(event: MouseEvent) {
      if (popoverRef.current && !popoverRef.current.contains(event.target as Node)) {
        setIsOpen(false);
      }
    }
    document.addEventListener("mousedown", handleClickOutside);
    return () => document.removeEventListener("mousedown", handleClickOutside);
  }, []);

  if (!isAuthenticated) return null;

  const { status, cloud_available, pending_count, failed_count, last_synced_at, last_error } =
    syncState;

  // Render badge config
  const getBadgeConfig = () => {
    if (isSyncing || status === "syncing") {
      return {
        bg: "bg-amber-50 text-amber-800 border-amber-200",
        dot: "bg-amber-500 animate-pulse",
        label: "Syncing...",
      };
    }
    if (status === "offline" || !cloud_available) {
      return {
        bg: "bg-slate-100 text-slate-700 border-slate-300",
        dot: "bg-slate-400",
        label: "Offline (Local)",
      };
    }
    if (status === "error" || failed_count > 0) {
      return {
        bg: "bg-rose-50 text-rose-700 border-rose-200",
        dot: "bg-rose-500",
        label: failed_count > 0 ? `${failed_count} Sync Issue${failed_count > 1 ? "s" : ""}` : "Sync Error",
      };
    }
    if (status === "pending" || pending_count > 0) {
      return {
        bg: "bg-sky-50 text-sky-700 border-sky-200",
        dot: "bg-sky-500 animate-ping",
        label: `${pending_count} Pending`,
      };
    }
    return {
      bg: "bg-emerald-50 text-emerald-700 border-emerald-200",
      dot: "bg-emerald-500",
      label: "Synced",
    };
  };

  const badge = getBadgeConfig();

  const formatLastSync = (timestamp: string | null) => {
    if (!timestamp) return "Never";
    try {
      const date = new Date(timestamp);
      return date.toLocaleTimeString([], { hour: "2-digit", minute: "2-digit", second: "2-digit" });
    } catch {
      return timestamp;
    }
  };

  return (
    <div className="relative" ref={popoverRef}>
      <button
        onClick={() => setIsOpen(!isOpen)}
        title="DietSense Cloud & Local Synchronization Status"
        className={`inline-flex items-center gap-1.5 px-2.5 py-1 rounded-full border text-xs font-medium transition-all shadow-sm hover:opacity-90 ${badge.bg}`}
      >
        <span className={`w-2 h-2 rounded-full ${badge.dot}`} />
        <span>{badge.label}</span>
      </button>

      {isOpen && (
        <div className="absolute right-0 mt-2 w-72 rounded-2xl bg-white border border-[#e2d6c9] shadow-xl p-4 z-50 animate-in fade-in zoom-in-95 duration-150">
          <div className="flex items-center justify-between pb-2 border-b border-slate-100">
            <span className="text-xs font-semibold uppercase tracking-wider text-slate-500">
              Cloud Sync Status
            </span>
            <span
              className={`text-[10px] px-2 py-0.5 rounded-full font-semibold ${
                cloud_available
                  ? "bg-emerald-100 text-emerald-800"
                  : "bg-slate-100 text-slate-600"
              }`}
            >
              {cloud_available ? "Supabase Online" : "Supabase Offline"}
            </span>
          </div>

          <div className="py-3 space-y-2 text-xs text-slate-600">
            <div className="flex justify-between items-center">
              <span>Local Storage:</span>
              <span className="font-medium text-slate-800">SQLite (Primary)</span>
            </div>
            <div className="flex justify-between items-center">
              <span>Pending Queue:</span>
              <span className={`font-semibold ${pending_count > 0 ? "text-sky-600" : "text-slate-700"}`}>
                {pending_count} item{pending_count === 1 ? "" : "s"}
              </span>
            </div>
            {failed_count > 0 && (
              <div className="flex justify-between items-center text-rose-600">
                <span>Failed Queue:</span>
                <span className="font-semibold">{failed_count} item{failed_count === 1 ? "" : "s"}</span>
              </div>
            )}
            <div className="flex justify-between items-center">
              <span>Last Synced:</span>
              <span className="font-mono text-[11px] text-slate-700">
                {formatLastSync(last_synced_at)}
              </span>
            </div>

            {last_error && (
              <div className="mt-2 p-2 bg-rose-50 border border-rose-100 rounded-lg text-[11px] text-rose-700 break-words leading-tight">
                ⚠️ {last_error}
              </div>
            )}
          </div>

          <div className="pt-2 border-t border-slate-100 flex gap-2">
            <button
              onClick={() => triggerSync()}
              disabled={isSyncing}
              className="flex-1 py-1.5 px-3 bg-[#581825] hover:bg-[#421018] text-white rounded-xl text-xs font-medium transition disabled:opacity-50 shadow-sm"
            >
              {isSyncing ? "Syncing..." : "Sync Now"}
            </button>
            {failed_count > 0 && (
              <button
                onClick={() => retryFailedSync()}
                disabled={isSyncing}
                className="py-1.5 px-3 bg-amber-600 hover:bg-amber-700 text-white rounded-xl text-xs font-medium transition disabled:opacity-50 shadow-sm"
              >
                Retry
              </button>
            )}
          </div>
        </div>
      )}
    </div>
  );
};
