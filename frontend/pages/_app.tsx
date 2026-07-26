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
import { getUserNameFromToken } from "@/lib/auth";
import { ToastProvider } from "@/components/ToastProvider";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { useState } from "react";

// 不包裹 Layout 的路由（独立设计或登录相关）
const LAYOUT_EXCLUDE_PATHS = new Set<string>([
  "/",          // 登录页（重定向占位 · T6）
  "/auth",      // 注册/登录页（T5 · 决策 6 + spec.md § 5 路由契约）
  "/onboarding", // 注册/引导
]);

// P1-6: Web Vitals console-only 上报 (不接 web-vitals 库, 不引新依赖)
if (typeof window !== "undefined") {
  try {
    const reportWebVital = (metric: { name: string; value: number; id: string }) => {
      // eslint-disable-next-line no-console
      console.log("[web-vitals]", metric.name, metric.value)
    }
    // 注: reportWebVitals 实际接入需 web-vitals 库; 这里仅占位
    // 等 web-vitals 加进 deps 后再 enable
    void reportWebVital
  } catch (e) {
    // ignore
  }
}

export default function App({ Component, pageProps }: AppProps) {
  const router = useRouter();
  const [queryClient] = useState(() => new QueryClient());

  // SSR + 客户端一致判断：用 router.pathname（同步可用）+ token 同步检查
  const hasToken = typeof window !== "undefined" ? !!getToken() : true;
  const shouldWrapLayout =
    hasToken && !LAYOUT_EXCLUDE_PATHS.has(router.pathname);

  // T2 + T3 · 决策 8 方案 A：从 JWT email 前缀派生 userName（去 hardcode "开发者"）
  // SSR 时 getToken() 返回 null → userName fallback "用户"（中性 fallback · 满足 Layout 必填）
  // 应该WrapLayout=false 路径（登录页）不渲染 Layout → fallback 不会触发
  const userName = (hasToken ? getUserNameFromToken(getToken()) : null) ?? "用户";

  if (!shouldWrapLayout) {
    return (
      <QueryClientProvider client={queryClient}>
        <ToastProvider />
        <Component {...pageProps} />
      </QueryClientProvider>
    );
  }

  return (
    <QueryClientProvider client={queryClient}>
      <ToastProvider />
      <Layout currentPage={router.pathname} userName={userName}>
        <Component {...pageProps} />
      </Layout>
    </QueryClientProvider>
  );
}
