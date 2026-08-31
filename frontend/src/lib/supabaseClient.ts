/**
 * Supabase client utilities for DietSense frontend.
 *
 * Uses @supabase/ssr for proper Next.js 14 App Router integration.
 * - createBrowserClient: use in Client Components ("use client")
 * - See backend for server-side / service role usage.
 */

import { createBrowserClient } from "@supabase/ssr";

const supabaseUrl = process.env.NEXT_PUBLIC_SUPABASE_URL!;
const supabaseAnonKey = process.env.NEXT_PUBLIC_SUPABASE_ANON_KEY!;

if (!supabaseUrl || !supabaseAnonKey) {
  throw new Error(
    "Missing Supabase environment variables. " +
      "Copy .env.example to .env.local and fill in your Supabase project credentials."
  );
}

/**
 * Browser-side Supabase client.
 * Use in Client Components for auth, realtime, and row-level-secured queries.
 */
export function createClient() {
  return createBrowserClient(supabaseUrl, supabaseAnonKey);
}
