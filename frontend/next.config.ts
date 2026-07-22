import type { NextConfig } from "next";

const nextConfig: NextConfig = {
  output: "standalone",
  transpilePackages: ["@livekit/components-react", "livekit-client"],
  // 2026-07-22 audit 修复 · 让浏览器 fetch /api/* 直接走 backend
  // 避免 dev-login / digest endpoints 跨 origin（之前需要绝对 URL）
  async rewrites() {
    return [
      {
        source: "/api/:path*",
        destination: "http://localhost:8000/api/:path*",
      },
    ];
  },
};

export default nextConfig;
