import type { NextConfig } from "next";

const nextConfig: NextConfig = {
  output: "standalone",
  transpilePackages: ["@livekit/components-react", "livekit-client"],
};

export default nextConfig;
