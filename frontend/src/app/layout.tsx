import type { Metadata } from "next";
import "./globals.css";
import { AuthProvider } from "@/context/AuthContext";
import { AtmosphereShader } from "@/components/shader/AtmosphereShader";

export const metadata: Metadata = {
  title: "DietSense — Adaptive AI Meal Planning",
  description:
    "Evidence-based, personalized meal planning for obesity prevention. Powered by USDA/ICMR-NIN nutrition data and adaptive AI.",
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="en">
      <body className="min-h-screen bg-[#faf7f2] font-sans antialiased relative overflow-x-hidden selection:bg-[#581825] selection:text-white">
        <AuthProvider>
          <AtmosphereShader />
          {children}
        </AuthProvider>
      </body>
    </html>
  );
}
