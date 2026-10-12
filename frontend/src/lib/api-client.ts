/**
 * DietSense - API Client
 * Fetch wrapper that attaches Supabase JWT to requests directed to the FastAPI backend.
 */

import { createClient } from "./supabaseClient";

const API_BASE_URL =
  process.env.NEXT_PUBLIC_API_BASE_URL ||
  process.env.NEXT_PUBLIC_API_URL ||
  "http://localhost:8000";

export async function apiClient<T>(endpoint: string, options: RequestInit = {}): Promise<T> {
  let token: string | null = null;
  try {
    const supabase = createClient();
    const { data: { session } } = await supabase.auth.getSession();
    token = session?.access_token || null;
  } catch {
    // If running outside browser or before initialization
    token = null;
  }

  const headers = new Headers(options.headers || {});
  headers.set("Content-Type", "application/json");

  if (token) {
    headers.set("Authorization", `Bearer ${token}`);
  }

  const response = await fetch(`${API_BASE_URL}${endpoint}`, {
    ...options,
    headers,
  });

  if (!response.ok) {
    let errorDetail = response.statusText;
    try {
      const errJson = await response.json();
      if (errJson && errJson.detail) {
        errorDetail = errJson.detail;
      }
    } catch {
      // fallback to statusText
    }
    throw new Error(`API Error (${response.status}): ${errorDetail}`);
  }

  return response.json() as Promise<T>;
}
