/**
 * Interview Setup — configure and launch a voice interview.
 */

import { useState } from "react";
import { useRouter } from "next/router";
import { getToken, startInterview } from "@/lib/api";

export default function InterviewSetup() {
  const router = useRouter();
  const [round, setRound] = useState("round1");
  const [starting, setStarting] = useState(false);
  const [error, setError] = useState("");

  const handleStart = async () => {
    setStarting(true);
    setError("");
    try {
      const interview = await startInterview(round);
      // Navigate to voice interview room
      router.push(`/interview/room?id=${interview.id}`);
    } catch (e: any) {
      setError(e.message || "启动失败");
      setStarting(false);
    }
  };

  return (
    <div className="min-h-screen bg-[#050914] text-[#f1f5f9] flex flex-col">
      <nav className="flex items-center gap-4 px-6 py-3.5 bg-[#0c1024]/90 backdrop-blur-xl border-b border-indigo-500/10">
        <button onClick={() => router.push("/interview/profile")} className="text-gray-400 hover:text-white text-sm">← 返回</button>
        <span className="text-lg font-bold bg-gradient-to-r from-indigo-400 to-purple-400 bg-clip-text text-transparent">面试配置</span>
      </nav>

      <main className="flex-1 flex items-center justify-center px-6">
        <div className="bg-white/[0.03] backdrop-blur-xl border border-indigo-500/10 rounded-2xl p-10 max-w-md w-full text-center">
          <div className="text-5xl mb-6">🎯</div>
          <h2 className="text-2xl font-bold mb-2">开始语音面试</h2>
          <p className="text-gray-400 text-sm mb-8">全双工实时对话 · AI 追问引擎 · 面试官 Alex</p>

          <div className="space-y-4 text-left">
            <div>
              <label className="block text-sm text-gray-400 mb-2">面试轮次</label>
              <div className="flex gap-3">
                {[
                  { v: "round1", l: "一轮面试", d: "基础 + 广度，8 题" },
                  { v: "round2", l: "二轮面试", d: "深入 + 追问，5 题" },
                ].map(r => (
                  <button key={r.v} onClick={() => setRound(r.v)}
                    className={`flex-1 p-4 rounded-xl border text-left transition-all ${
                      round === r.v
                        ? "bg-indigo-500/20 border-indigo-500/40 text-white"
                        : "bg-white/[0.02] border-gray-700/20 text-gray-400 hover:border-indigo-500/20"
                    }`}
                  >
                    <div className="font-medium text-sm">{r.l}</div>
                    <div className="text-xs mt-1 opacity-70">{r.d}</div>
                  </button>
                ))}
              </div>
            </div>

            {error && <div className="text-red-400 text-sm text-center py-2">{error}</div>}

            <button
              onClick={handleStart}
              disabled={starting}
              className="w-full py-4 rounded-xl font-medium text-base bg-gradient-to-r from-indigo-500 to-purple-500 text-white shadow-lg shadow-purple-500/20 hover:opacity-90 transition-all disabled:opacity-50"
            >
              {starting ? "正在创建面试..." : "🎤 开始语音面试"}
            </button>

            <p className="text-xs text-gray-600 text-center">
              点击后立即进入通话 · 请允许麦克风权限
            </p>
          </div>
        </div>
      </main>
    </div>
  );
}
