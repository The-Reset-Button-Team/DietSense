/**
 * DietSense - API Client
 * Fetch wrapper that attaches Supabase JWT to requests directed to the FastAPI backend.
 */

const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

export async function apiClient<T>(endpoint: string, options: RequestInit = {}): Promise<T> {
  // TODO: Retrieve token from Supabase session (e.g., supabase.auth.getSession())
  const token: string | null = null;

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
    throw new Error(`API Error: ${response.statusText}`);
  }

  return response.json() as Promise<T>;
}
