import { useRouter } from "next/router";
import { useEffect, useState } from "react";
import { getGitHubLoginUrl, devLogin, getProfile, getToken, clearToken, handleGitHubCallback, login, register } from "@/lib/api";

type AuthMode = "login" | "register";

export default function Home() {
  const router = useRouter();
  const [loading, setLoading] = useState(true);
  const [submitting, setSubmitting] = useState(false);
  const [error, setError] = useState("");
  const [mode, setMode] = useState<AuthMode>("login");

  // Form state
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [displayName, setDisplayName] = useState("");

  useEffect(() => {
    const code = router.query.code as string;
    if (code) {
      handleGitHubCallback(code)
        .then((data) => data.user && router.push("/dashboard"))
        .catch(() => setLoading(false));
    } else if (getToken()) {
      getProfile()
        .then(() => router.push("/dashboard"))
        .catch(() => { clearToken(); setLoading(false); });
    } else {
      setLoading(false);
    }
  }, [router.query]);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError("");
    setSubmitting(true);
    try {
      const fn = mode === "register" ? register : login;
      const data = await (mode === "register"
        ? register(email, password, displayName)
        : login(email, password));
      if (data.user) router.push("/dashboard");
    } catch (err: any) {
      setError(err.message || "操作失败");
    } finally {
      setSubmitting(false);
    }
  };

  const githubLogin = async () => {
    const { url } = await getGitHubLoginUrl();
    window.location.href = url;
  };

  if (loading) {
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

  return (
    <div className="min-h-screen gradient-page flex flex-col items-center justify-center text-white px-4">
      <div className="text-center space-y-6 max-w-md w-full">
        {/* Logo & Title */}
        <div className="space-y-3">
          <div className="w-14 h-14 mx-auto rounded-2xl gradient-accent flex items-center justify-center shadow-lg shadow-purple-500/30">
            <svg className="w-7 h-7 text-white" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={1.5}>
              <path strokeLinecap="round" strokeLinejoin="round" d="M8.625 12a.375.375 0 11-.75 0 .375.375 0 01.75 0zm0 0H8.25m4.125 0a.375.375 0 11-.75 0 .375.375 0 01.75 0zm0 0H12m4.125 0a.375.375 0 11-.75 0 .375.375 0 01.75 0zm0 0h-.375M21 12c0 4.556-4.03 8.25-9 8.25a9.764 9.764 0 01-2.555-.337A5.972 5.972 0 015.41 20.97a5.969 5.969 0 01-.474-.065 4.48 4.48 0 00.978-2.025c.09-.457-.133-.901-.467-1.226C3.93 16.178 3 14.189 3 12c0-4.556 4.03-8.25 9-8.25s9 3.694 9 8.25z" />
            </svg>
          </div>
          <h1 className="text-4xl font-bold bg-gradient-to-r from-indigo-400 via-purple-400 to-pink-400 bg-clip-text text-transparent">
            KnockWise
          </h1>
          <p className="text-sm text-gray-400">AI 面试官 · 真正会追问</p>
        </div>

        {/* Mode tabs */}
        <div className="flex rounded-xl bg-gray-800/50 p-1 border border-gray-700/30">
          <button
            onClick={() => { setMode("login"); setError(""); }}
            className={`flex-1 py-2.5 text-sm font-medium rounded-lg transition-all ${mode === "login" ? "bg-indigo-500/20 text-indigo-300" : "text-gray-400 hover:text-gray-200"}`}
          >登录</button>
          <button
            onClick={() => { setMode("register"); setError(""); }}
            className={`flex-1 py-2.5 text-sm font-medium rounded-lg transition-all ${mode === "register" ? "bg-indigo-500/20 text-indigo-300" : "text-gray-400 hover:text-gray-200"}`}
          >注册</button>
        </div>

        {/* Email/Password Form */}
        <form onSubmit={handleSubmit} className="space-y-4 text-left">
          {mode === "register" && (
            <div>
              <label className="block text-sm text-gray-400 mb-1.5">昵称</label>
              <input
                type="text" value={displayName} onChange={e => setDisplayName(e.target.value)}
                required
                className="w-full px-4 py-3 rounded-xl bg-gray-800/50 border border-gray-700/30 text-white placeholder-gray-500 focus:border-indigo-500 focus:outline-none transition-colors"
                placeholder="你的昵称"
              />
            </div>
          )}
          <div>
            <label className="block text-sm text-gray-400 mb-1.5">邮箱</label>
            <input
              type="email" value={email} onChange={e => setEmail(e.target.value)}
              required
              className="w-full px-4 py-3 rounded-xl bg-gray-800/50 border border-gray-700/30 text-white placeholder-gray-500 focus:border-indigo-500 focus:outline-none transition-colors"
              placeholder="user@example.com"
            />
          </div>
          <div>
            <label className="block text-sm text-gray-400 mb-1.5">密码</label>
            <input
              type="password" value={password} onChange={e => setPassword(e.target.value)}
              required minLength={6}
              className="w-full px-4 py-3 rounded-xl bg-gray-800/50 border border-gray-700/30 text-white placeholder-gray-500 focus:border-indigo-500 focus:outline-none transition-colors"
              placeholder="••••••••"
            />
          </div>
          {error && <p className="text-red-400 text-sm text-center">{error}</p>}
          <button
            type="submit" disabled={submitting}
            className="w-full py-3 rounded-xl font-medium gradient-accent hover:opacity-90 shadow-lg shadow-purple-500/30 transition-all disabled:opacity-50"
          >
            {submitting ? "请稍候..." : mode === "register" ? "注  册" : "登  录"}
          </button>
        </form>

        {/* Divider */}
        <div className="flex items-center gap-3 text-gray-500 text-xs">
          <div className="flex-1 h-px bg-gray-700/50" />
          <span>或</span>
          <div className="flex-1 h-px bg-gray-700/50" />
        </div>

        {/* GitHub OAuth */}
        <button
          onClick={githubLogin}
          className="flex items-center gap-3 mx-auto px-8 py-3 w-full justify-center rounded-xl font-medium border border-gray-700/30 bg-gray-800/30 hover:bg-gray-700/40 text-gray-300 transition-all"
        >
          <svg className="w-5 h-5" fill="currentColor" viewBox="0 0 24 24">
            <path d="M12 0c-6.626 0-12 5.373-12 12 0 5.302 3.438 9.8 8.207 11.387.599.111.793-.261.793-.577v-2.234c-3.338.726-4.033-1.416-4.033-1.416-.546-1.387-1.333-1.756-1.333-1.756-1.089-.745.083-.729.083-.729 1.205.084 1.839 1.237 1.839 1.237 1.07 1.834 2.807 1.304 3.492.997.107-.775.418-1.305.762-1.604-2.665-.305-5.467-1.334-5.467-5.931 0-1.311.469-2.381 1.236-3.221-.124-.303-.535-1.524.117-3.176 0 0 1.008-.322 3.301 1.23.957-.266 1.983-.399 3.003-.404 1.02.005 2.047.138 3.006.404 2.291-1.552 3.297-1.23 3.297-1.23.653 1.653.242 2.874.118 3.176.77.84 1.235 1.911 1.235 3.221 0 4.609-2.807 5.624-5.479 5.921.43.372.823 1.102.823 2.222v3.293c0 .319.192.694.801.576 4.765-1.589 8.199-6.086 8.199-11.386 0-6.627-5.373-12-12-12z" />
          </svg>
          GitHub 登录
        </button>

        {/* Dev Login */}
        <button
          onClick={() => devLogin("dev_user").then(() => router.push("/dashboard"))}
          className="w-full py-2.5 rounded-xl text-xs text-gray-500 hover:text-gray-300 border border-gray-700/20 hover:border-gray-600/40 transition-all"
        >
          Dev Login (跳过认证)
        </button>
      </div>
    </div>
  );
}
