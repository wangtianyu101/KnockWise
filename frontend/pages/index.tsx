import { useRouter } from "next/router";
import { useEffect, useState } from "react";
import { getGitHubLoginUrl, devLogin, getProfile, getToken, clearToken, handleGitHubCallback } from "@/lib/api";

export default function Home() {
  const router = useRouter();
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const code = router.query.code as string;
    if (code) {
      handleGitHubCallback(code)
        .then((data) => {
          if (data.user) router.push("/onboarding");
        })
        .catch(() => setLoading(false));
    } else if (getToken()) {
      getProfile()
        .then(() => router.push("/onboarding"))
        .catch(() => { clearToken(); setLoading(false); });
    } else {
      setLoading(false);
    }
  }, [router.query]);

  const login = async () => {
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
    <div className="min-h-screen gradient-page flex flex-col items-center justify-center text-white">
      <div className="text-center space-y-8 max-w-md px-6">
        {/* Logo & Title */}
        <div className="space-y-4">
          <div className="w-16 h-16 mx-auto rounded-2xl gradient-accent flex items-center justify-center shadow-lg shadow-purple-500/30">
            <svg className="w-8 h-8 text-white" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={1.5}>
              <path strokeLinecap="round" strokeLinejoin="round" d="M8.625 12a.375.375 0 11-.75 0 .375.375 0 01.75 0zm0 0H8.25m4.125 0a.375.375 0 11-.75 0 .375.375 0 01.75 0zm0 0H12m4.125 0a.375.375 0 11-.75 0 .375.375 0 01.75 0zm0 0h-.375M21 12c0 4.556-4.03 8.25-9 8.25a9.764 9.764 0 01-2.555-.337A5.972 5.972 0 015.41 20.97a5.969 5.969 0 01-.474-.065 4.48 4.48 0 00.978-2.025c.09-.457-.133-.901-.467-1.226C3.93 16.178 3 14.189 3 12c0-4.556 4.03-8.25 9-8.25s9 3.694 9 8.25z" />
            </svg>
          </div>
          <div>
            <h1 className="text-5xl font-bold bg-gradient-to-r from-indigo-400 via-purple-400 to-pink-400 bg-clip-text text-transparent">
              CodeMock
            </h1>
            <p className="text-lg text-gray-400 mt-2">AI 面试官 · 真正会追问</p>
          </div>
        </div>

        {/* Feature tags */}
        <div className="flex flex-wrap justify-center gap-2">
          {["实时语音", "追问引擎", "雷达报告", "AI Agent"].map((tag) => (
            <span
              key={tag}
              className="px-3 py-1 text-xs rounded-full bg-indigo-500/10 text-indigo-300 border border-indigo-500/20"
            >
              {tag}
            </span>
          ))}
        </div>

        <p className="text-gray-500 text-sm leading-relaxed">
          模拟真实技术面试，AI 面试官根据你的回答动态追问。
          覆盖 AI Agent、RAG、LangGraph、Java 等技术方向。
        </p>

        {/* Login buttons */}
        <div className="space-y-3">
          <button
            onClick={login}
            className="flex items-center gap-3 mx-auto px-8 py-4 w-full justify-center rounded-xl font-medium transition-all duration-200 gradient-accent hover:opacity-90 shadow-lg shadow-purple-500/30"
          >
            <svg className="w-5 h-5" fill="currentColor" viewBox="0 0 24 24">
              <path d="M12 0c-6.626 0-12 5.373-12 12 0 5.302 3.438 9.8 8.207 11.387.599.111.793-.261.793-.577v-2.234c-3.338.726-4.033-1.416-4.033-1.416-.546-1.387-1.333-1.756-1.333-1.756-1.089-.745.083-.729.083-.729 1.205.084 1.839 1.237 1.839 1.237 1.07 1.834 2.807 1.304 3.492.997.107-.775.418-1.305.762-1.604-2.665-.305-5.467-1.334-5.467-5.931 0-1.311.469-2.381 1.236-3.221-.124-.303-.535-1.524.117-3.176 0 0 1.008-.322 3.301 1.23.957-.266 1.983-.399 3.003-.404 1.02.005 2.047.138 3.006.404 2.291-1.552 3.297-1.23 3.297-1.23.653 1.653.242 2.874.118 3.176.77.84 1.235 1.911 1.235 3.221 0 4.609-2.807 5.624-5.479 5.921.43.372.823 1.102.823 2.222v3.293c0 .319.192.694.801.576 4.765-1.589 8.199-6.086 8.199-11.386 0-6.627-5.373-12-12-12z" />
            </svg>
            Sign in with GitHub
          </button>

          <button
            onClick={() => devLogin("dev_user").then(() => router.push("/onboarding"))}
            className="w-full px-6 py-3 rounded-xl font-medium text-sm text-gray-400 hover:text-gray-200 bg-gray-800/50 hover:bg-gray-700/50 border border-gray-700/30 transition-all duration-200"
          >
            Dev Login (Skip GitHub)
          </button>
        </div>
      </div>
    </div>
  );
}
