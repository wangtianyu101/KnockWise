/**
 * pages/index.tsx — T6 路由迁移
 *
 * 决策 6（路径 B 实际对象）：迁 `/` → `/auth`
 *
 * 行为：
 * - 用户访问 `http://localhost:3000/` → router.replace('/auth')
 * - `_app.tsx` LAYOUT_EXCLUDE_PATHS 含 `/` → 不包 Layout（auth 页独立设计）
 *
 * 设计要点（spec.md § 6 AC-3）：
 * - SSR + 客户端一致判断：用 router.pathname（同步可用）
 * - hasToken 短路：有 token → 不重定向（避免循环 · 但实际 _app.tsx 应先跳 dashboard）
 * - 客户端首帧不闪（router.replace 不 push · 无 history entry）
 */
import { useRouter } from "next/router";
import { useEffect } from "react";
import { getToken } from "@/lib/api";

export default function Index() {
  const router = useRouter();

  useEffect(() => {
    // 有 token → 跳 dashboard（避免已登录用户看到 auth 页）
    // 无 token → 跳 /auth
    if (getToken()) {
      router.replace("/dashboard");
    } else {
      router.replace("/auth");
    }
  }, [router]);

  // 重定向中显示 loading（不渲染实际内容）
  return (
    <div className="min-h-screen gradient-page flex items-center justify-center">
      <div className="flex items-center gap-2">
        <div className="w-3 h-3 bg-indigo-500 rounded-full animate-bounce" style={{ animationDelay: "0ms" }} />
        <div className="w-3 h-3 bg-purple-500 rounded-full animate-bounce" style={{ animationDelay: "150ms" }} />
        <div className="w-3 h-3 bg-indigo-500 rounded-full animate-bounce" style={{ animationDelay: "300ms" }} />
      </div>
    </div>
  );
}