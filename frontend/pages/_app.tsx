/**
 * _app.tsx — V3.8 P1 注入 Layout
 *
 * V3.8 重构：
 * - 默认所有 page 包裹 <Layout>
 * - 例外：登录页 (/)、注册/登录页 (/onboarding) 不包裹（独立设计）
 * - 未登录用户：不包裹（避免 Sidebar 闪一下再跳登录）
 *
 * 决策：用 router.pathname 判断（避免 useEffect 异步导致的 hydration mismatch）
 */
import type { AppProps } from "next/app";
import { useRouter } from "next/router";
import "@/styles/globals.css";
import { Layout } from "@/components/v3/Layout/Layout";
import { getToken } from "@/lib/api";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { useState } from "react";

// 不包裹 Layout 的路由（独立设计或登录相关）
const LAYOUT_EXCLUDE_PATHS = new Set<string>([
  "/",          // 登录页
  "/onboarding", // 注册/引导
]);

export default function App({ Component, pageProps }: AppProps) {
  const router = useRouter();
  const [queryClient] = useState(() => new QueryClient());

  // SSR + 客户端一致判断：用 router.pathname（同步可用）+ token 同步检查
  const hasToken = typeof window !== "undefined" ? !!getToken() : true;
  const shouldWrapLayout =
    hasToken && !LAYOUT_EXCLUDE_PATHS.has(router.pathname);

  if (!shouldWrapLayout) {
    return (
      <QueryClientProvider client={queryClient}>
        <Component {...pageProps} />
      </QueryClientProvider>
    );
  }

  return (
    <QueryClientProvider client={queryClient}>
      <Layout currentPage={router.pathname}>
        <Component {...pageProps} />
      </Layout>
    </QueryClientProvider>
  );
}
