/**
 * DietSense — Local API Client
 * Clean fetch wrapper for the local FastAPI backend.
 * Uses secure cookie credentials ("include") for session handling.
 */

const API_BASE_URL =
  process.env.NEXT_PUBLIC_API_BASE_URL ||
  process.env.NEXT_PUBLIC_API_URL ||
  "http://localhost:8000";

let _inMemoryToken: string | null = null;

export function setApiAuthToken(token: string | null) {
  _inMemoryToken = token;
}

export function getApiAuthToken(): string | null {
  return _inMemoryToken;
}

export async function apiClient<T>(endpoint: string, options: RequestInit = {}): Promise<T> {
  const headers = new Headers(options.headers || {});

  if (!headers.has("Content-Type") && !(options.body instanceof FormData)) {
    headers.set("Content-Type", "application/json");
  }

  // Attach token header if present in memory (complements HttpOnly session cookie)
  if (_inMemoryToken && !headers.has("Authorization")) {
    headers.set("Authorization", `Bearer ${_inMemoryToken}`);
  }

  const response = await fetch(`${API_BASE_URL}${endpoint}`, {
    ...options,
    headers,
    credentials: "include", // Transmit HttpOnly session cookies
  });

  if (!response.ok) {
    let errorDetail = response.statusText;
    try {
      const errJson = await response.json();
      if (errJson && errJson.detail) {
        errorDetail = typeof errJson.detail === "string" ? errJson.detail : JSON.stringify(errJson.detail);
      }
    } catch {
      // fallback to statusText
    }
    throw new Error(`API Error (${response.status}): ${errorDetail}`);
  }

  return response.json() as Promise<T>;
}
