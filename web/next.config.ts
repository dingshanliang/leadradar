import type { NextConfig } from "next";

const nextConfig: NextConfig = {
  // Enable statically typed routes for type-safe link components
  // (stable in Next.js 16, no longer under experimental)
  typedRoutes: true,

  images: {
    remotePatterns: [
      {
        protocol: "http",
        hostname: "localhost",
      },
    ],
  },
};

export default nextConfig;
