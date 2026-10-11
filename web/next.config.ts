import type { NextConfig } from "next";

const nextConfig: NextConfig = {
  cacheComponents: true,
  partialPrefetching: true,
  images: {
    // Product images come straight from each store's CDN.
    remotePatterns: [
      { protocol: "https", hostname: "shared.akamai.steamstatic.com" },
      { protocol: "https", hostname: "store-images.s-microsoft.com" },
      { protocol: "https", hostname: "cdn-shop.adafruit.com" },
      { protocol: "https", hostname: "www.sparkfun.com" },
    ],
  },
  turbopack: {
    rules: {
      "*.css": {
        loaders: ["@tailwindcss/turbopack"],
        as: "*.css",
      },
    },
  },
};

export default nextConfig;
