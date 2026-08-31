import type { NextConfig } from "next";

const nextConfig: NextConfig = {
  // Allow images from Supabase storage and external food image CDNs
  images: {
    remotePatterns: [
      {
        protocol: "https",
        hostname: "*.supabase.co",
        port: "",
        pathname: "/storage/v1/object/public/**",
      },
    ],
  },
  // Strict mode for catching potential issues early
  reactStrictMode: true,
};

export default nextConfig;
