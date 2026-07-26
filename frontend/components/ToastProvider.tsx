/**
 * ToastProvider · sonner Toaster 封装（next/dynamic ssr:false）
 *
 * 设计要点（决策 5 + CLAUDE.md § 6.7 verify-loop）：
 * - sonner Toaster 必须客户端渲染（避免 Next.js SSR 报错 "document is not defined"）
 * - 用 next/dynamic + ssr:false 包裹原 Toaster
 * - re-export 简化上层调用（_app.tsx 直接 import ToastProvider 即可）
 *
 * 用法：
 *   // _app.tsx
 *   import { ToastProvider } from "@/components/ToastProvider";
 *   ...
 *   <ToastProvider position="top-center" richColors />
 */
"use client";

import dynamic from "next/dynamic";
import type { ComponentProps } from "react";

// next/dynamic ssr:false 包裹 sonner Toaster（避免 SSR 报错）
const SonnerToaster = dynamic(
  () => import("sonner").then((m) => m.Toaster),
  { ssr: false }
);

export type ToastProviderProps = ComponentProps<typeof SonnerToaster>;

export function ToastProvider(props: ToastProviderProps) {
  return <SonnerToaster {...props} />;
}

export default ToastProvider;