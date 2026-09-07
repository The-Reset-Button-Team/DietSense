/**
 * Supabase client utilities for DietSense frontend.
 *
 * Uses @supabase/ssr for proper Next.js App Router integration.
 * - createBrowserClient: use in Client Components ("use client")
 */

import { createBrowserClient } from "@supabase/ssr";

const supabaseUrl = process.env.NEXT_PUBLIC_SUPABASE_URL || "https://placeholder-project.supabase.co";
const supabaseAnonKey = process.env.NEXT_PUBLIC_SUPABASE_ANON_KEY || "placeholder-anon-key";

/**
 * Browser-side Supabase client.
 * Use in Client Components for auth, realtime, and row-level-secured queries.
 */
export function createClient() {
  return createBrowserClient(supabaseUrl, supabaseAnonKey);
}
