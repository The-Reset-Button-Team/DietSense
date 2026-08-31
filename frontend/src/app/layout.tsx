import type { Metadata } from "next";
import "./globals.css";

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
      <body className="min-h-screen bg-gray-50 font-sans antialiased">
        {children}
      </body>
    </html>
  );
}
