/**
 * pages/auth.tsx — T5 · 单一表单 + 自动判断登录/注册（决策 10/11/12）
 *
 * 设计要点（spec.md § 6 AC-1 + design-spec.md § 3 v4 视觉精简）：
 * - 单一表单 + onBlur 调 check-email → 自动切登录/注册态
 * - 默认态：标题"欢迎来到 KnockWise" + 邮箱 + 密码 + 按钮"登录 / 注册"
 * - 登录态：标题"欢迎回来" + 邮箱 readonly + 密码 autofocus + 按钮"登录"
 * - 注册态：标题"加入 KnockWise" + 邮箱 readonly + 昵称字段 + 密码 + 按钮"注册"
 * - 提交：调 authenticate() · mode="login" → "登录成功" · mode="register" → "创建成功" · 500ms 后跳转 /dashboard
 * - 失败：toast.error + 不跳转
 * - Logo = V3 K logo SVG（不是闪电 ⚡）
 * - Toast 图标 = SVG check / X（不是文字 ✓ ✕）
 * - 视觉 = V3 dark glassmorphism
 * - 卡片**只有标题**（无副标题 · 无检查状态指示器 · brand-block 无 tagline）
 */
import { useRouter } from "next/router";
import { useEffect, useState } from "react";
import { authenticate } from "@/lib/api";
import { toast } from "sonner";

type AuthMode = "default" | "login" | "register";

export default function Auth() {
  const router = useRouter();

  // 表单状态
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [displayName, setDisplayName] = useState("");
  const [mode, setMode] = useState<AuthMode>("default");
  const [submitting, setSubmitting] = useState(false);

  // onBlur 调 check-email → 自动判断 mode
  const handleEmailBlur = async (value: string) => {
    if (!value || !value.includes("@")) return;
    try {
      const resp = await fetch(
        `/api/auth/check-email?email=${encodeURIComponent(value)}`
      );
      if (!resp.ok) return; // 400 invalid email 等 · 不切状态
      const data = await resp.json();
      if (data.exists) {
        setMode("login");
      } else {
        setMode("register");
      }
    } catch {
      // 网络错误静默（toast.error 在提交时统一处理）
    }
  };

  // 提交
  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (submitting) return;
    setSubmitting(true);

    try {
      const data = await authenticate(
        email,
        password,
        mode === "register" ? displayName : undefined
      );
      // mode 字段决定 toast 文案（v5 决策 13 后端返回）
      const successMsg =
        data.mode === "register" ? "创建成功 · 正在跳转 Dashboard..." : "登录成功 · 正在跳转 Dashboard...";
      toast.success(successMsg);
      // 500ms 后跳转（给 toast 时间显示）
      setTimeout(() => {
        router.push("/dashboard");
      }, 500);
    } catch (err: any) {
      toast.error(err.message || "操作失败");
      // 不跳转 · 保留表单输入
    } finally {
      setSubmitting(false);
    }
  };

  return (
    <div className="min-h-screen gradient-page flex flex-col items-center justify-center text-white px-4">
      <div className="text-center space-y-6 max-w-md w-full">
        {/* Logo + 标题（V3 K logo · 无 tagline） */}
        <div className="space-y-3">
          <div className="w-14 h-14 mx-auto rounded-2xl gradient-accent flex items-center justify-center shadow-lg shadow-purple-500/30">
            {/* V3 K logo SVG（与 sidebar 一致） */}
            <svg width="28" height="28" viewBox="0 0 28 28" fill="none">
              <rect x="2" y="2" width="24" height="24" rx="7" fill="rgba(255,255,255,0.18)" />
              <path d="M9 7v14M9 21l11-14" stroke="white" strokeWidth="2.4" strokeLinecap="round" strokeLinejoin="round" />
              <path d="M14 14h6M20 14v7" stroke="white" strokeWidth="2.4" strokeLinecap="round" strokeLinejoin="round" opacity="0.65" />
            </svg>
          </div>
          <h1 className="text-4xl font-bold bg-gradient-to-r from-indigo-400 via-purple-400 to-pink-400 bg-clip-text text-transparent">
            KnockWise
          </h1>
        </div>

        {/* 单一表单（卡片只有标题 · 无副标题） */}
        <form onSubmit={handleSubmit} className="space-y-4 text-left">
          <h2 className="text-lg font-semibold text-white text-center mb-2">
            {mode === "login" ? "欢迎回来" : mode === "register" ? "加入 KnockWise" : "欢迎来到 KnockWise"}
          </h2>

          {/* 邮箱 */}
          <div>
            <label className="block text-sm text-gray-400 mb-1.5">邮箱</label>
            <input
              type="email"
              value={email}
              onChange={(e) => setEmail(e.target.value)}
              onBlur={(e) => handleEmailBlur(e.target.value)}
              required
              readOnly={mode !== "default"}
              className="w-full px-4 py-3 rounded-xl bg-gray-800/50 border border-gray-700/30 text-white placeholder-gray-500 focus:border-indigo-500 focus:outline-none transition-colors"
              placeholder="wangtianyu@example.com"
            />
          </div>

          {/* 昵称（仅注册态） */}
          {mode === "register" && (
            <div>
              <label className="block text-sm text-gray-400 mb-1.5">昵称（可选）</label>
              <input
                type="text"
                value={displayName}
                onChange={(e) => setDisplayName(e.target.value)}
                className="w-full px-4 py-3 rounded-xl bg-gray-800/50 border border-gray-700/30 text-white placeholder-gray-500 focus:border-indigo-500 focus:outline-none transition-colors"
                placeholder="你的昵称"
              />
            </div>
          )}

          {/* 密码 */}
          <div>
            <label className="block text-sm text-gray-400 mb-1.5">密码</label>
            <input
              type="password"
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              required
              minLength={6}
              autoFocus={mode !== "default"}
              className="w-full px-4 py-3 rounded-xl bg-gray-800/50 border border-gray-700/30 text-white placeholder-gray-500 focus:border-indigo-500 focus:outline-none transition-colors"
              placeholder="••••••"
            />
          </div>

          {/* 提交按钮（文字根据 mode 切换） */}
          <button
            type="submit"
            disabled={submitting}
            className="w-full py-3 rounded-xl font-medium gradient-accent hover:opacity-90 shadow-lg shadow-purple-500/30 transition-all disabled:opacity-50"
          >
            {submitting
              ? "请稍候..."
              : mode === "login"
              ? "登 录"
              : mode === "register"
              ? "注 册"
              : "登录 / 注册"}
          </button>
        </form>
      </div>
    </div>
  );
}