"use client";

import React, { createContext, useContext, useState, useEffect, useCallback } from "react";
import { apiClient } from "@/lib/api-client";
import { useAuth } from "./AuthContext";

export interface SyncStatus {
  status: "synced" | "pending" | "error" | "offline" | "syncing";
  cloud_available: boolean;
  pending_count: number;
  failed_count: number;
  last_synced_at: string | null;
  last_attempt_at: string | null;
  last_error: string | null;
}

interface SyncContextType {
  syncState: SyncStatus;
  isSyncing: boolean;
  triggerSync: () => Promise<boolean>;
  retryFailedSync: () => Promise<boolean>;
  refreshStatus: () => Promise<void>;
}

const DEFAULT_SYNC_STATUS: SyncStatus = {
  status: "synced",
  cloud_available: true,
  pending_count: 0,
  failed_count: 0,
  last_synced_at: null,
  last_attempt_at: null,
  last_error: null,
};

const SyncContext = createContext<SyncContextType | undefined>(undefined);

export const SyncProvider: React.FC<{ children: React.ReactNode }> = ({ children }) => {
  const { isAuthenticated, isLoading: authLoading } = useAuth();
  const [syncState, setSyncState] = useState<SyncStatus>(DEFAULT_SYNC_STATUS);
  const [isSyncing, setIsSyncing] = useState<boolean>(false);

  const refreshStatus = useCallback(async () => {
    if (!isAuthenticated || authLoading) return;

    try {
      const res = await apiClient<SyncStatus>("/api/sync/status");
      if (res) {
        setSyncState((prev) => ({
          ...res,
          status: isSyncing ? "syncing" : res.status,
        }));
      }
    } catch {
      // If endpoint is unreachable, mark status as offline
      setSyncState((prev) => ({
        ...prev,
        status: "offline",
        cloud_available: false,
      }));
    }
  }, [isAuthenticated, authLoading, isSyncing]);

  const triggerSync = useCallback(async (): Promise<boolean> => {
    if (!isAuthenticated) return false;

    setIsSyncing(true);
    setSyncState((prev) => ({ ...prev, status: "syncing" }));

    try {
      const res = await apiClient<{ status: string; result: any }>("/api/sync/trigger", {
        method: "POST",
      });
      await refreshStatus();
      return res.status === "success";
    } catch (err: any) {
      setSyncState((prev) => ({
        ...prev,
        status: "error",
        last_error: err?.message || "Sync failed",
      }));
      return false;
    } finally {
      setIsSyncing(false);
    }
  }, [isAuthenticated, refreshStatus]);

  const retryFailedSync = useCallback(async (): Promise<boolean> => {
    if (!isAuthenticated) return false;

    setIsSyncing(true);
    setSyncState((prev) => ({ ...prev, status: "syncing" }));

    try {
      const res = await apiClient<{ status: string; result: any }>("/api/sync/retry", {
        method: "POST",
      });
      await refreshStatus();
      return res.status === "success";
    } catch (err: any) {
      setSyncState((prev) => ({
        ...prev,
        status: "error",
        last_error: err?.message || "Retry failed",
      }));
      return false;
    } finally {
      setIsSyncing(false);
    }
  }, [isAuthenticated, refreshStatus]);

  // Initial fetch and periodic polling when authenticated
  useEffect(() => {
    if (!isAuthenticated || authLoading) return;

    refreshStatus();

    const interval = setInterval(() => {
      refreshStatus();
    }, 30000);

    return () => clearInterval(interval);
  }, [isAuthenticated, authLoading, refreshStatus]);

  // Network online/offline listeners for automatic synchronization recovery
  useEffect(() => {
    const handleOnline = () => {
      // Automatic synchronization triggered when connectivity returns
      if (isAuthenticated) {
        triggerSync();
      }
    };

    const handleOffline = () => {
      setSyncState((prev) => ({
        ...prev,
        status: "offline",
        cloud_available: false,
      }));
    };

    const handleFocus = () => {
      if (isAuthenticated) {
        refreshStatus();
      }
    };

    window.addEventListener("online", handleOnline);
    window.addEventListener("offline", handleOffline);
    window.addEventListener("focus", handleFocus);

    return () => {
      window.removeEventListener("online", handleOnline);
      window.removeEventListener("offline", handleOffline);
      window.removeEventListener("focus", handleFocus);
    };
  }, [isAuthenticated, triggerSync, refreshStatus]);

  return (
    <SyncContext.Provider
      value={{
        syncState,
        isSyncing,
        triggerSync,
        retryFailedSync,
        refreshStatus,
      }}
    >
      {children}
    </SyncContext.Provider>
  );
};

export const useSync = (): SyncContextType => {
  const context = useContext(SyncContext);
  if (!context) {
    throw new Error("useSync must be used within a SyncProvider");
  }
  return context;
};
