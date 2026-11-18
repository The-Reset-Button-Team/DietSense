import type { Metadata } from "next";
import "./globals.css";
import { AuthProvider } from "@/context/AuthContext";
import { SyncProvider } from "@/context/SyncContext";
import { AtmosphereShader } from "@/components/shader/AtmosphereShader";

export const metadata: Metadata = {
  title: "DietSense — Artisanal & Evidence-Based Nutrition Platform",
  description:
    "Evidence-based, personalized meal planning and metabolic tracking powered by USDA & ICMR-NIN verified nutrition data and adaptive AI.",
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="en">
      <head>
        <link rel="preconnect" href="https://fonts.googleapis.com" />
        <link rel="preconnect" href="https://fonts.gstatic.com" crossOrigin="" />
      </head>
      <body className="min-h-screen bg-surface font-body-md text-on-surface antialiased relative selection:bg-primary-fixed selection:text-on-primary-fixed">
        <AuthProvider>
          <SyncProvider>
            <AtmosphereShader />
            {children}
          </SyncProvider>
        </AuthProvider>
      </body>
    </html>
  );
}
