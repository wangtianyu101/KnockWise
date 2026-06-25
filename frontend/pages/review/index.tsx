/**
 * Review — 复习 tab (SRS 复习队列)
 *
 * 路由: /review
 * 功能: 拉 review_queue (SM-2 到期题) → 一题一题答 → 自动 SM-2 更新
 * 配套: docs/10-架构/面试题库-页面规划.md · 4.2 复习 tab
 */

import React, { useEffect, useState, useRef } from "react";
import { useRouter } from "next/router";
import { getToken } from "@/lib/api";

const API = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

interface ReviewItem {
  question_id: string;
  status: string;
  ease_factor: number;
  interval_days: number;
  next_review_at: string | null;
}

interface QuestionDetail {
  id: string;
  topic: string;
  sub_topic: string;
  difficulty: number;
  question_text: string;
  answer_key_points: string[];
}

export default function ReviewPage() {
  const router = useRouter();
  const [queue, setQueue] = useState<ReviewItem[]>([]);
  const [current, setCurrent] = useState<QuestionDetail | null>(null);
  const [userAnswer, setUserAnswer] = useState("");
  const [submitting, setSubmitting] = useState(false);
  const [loading, setLoading] = useState(true);
  const [completed, setCompleted] = useState(0);
  const [showHint, setShowHint] = useState(false);
  const [startTime, setStartTime] = useState<number>(0);

  const initRef = useRef(false);
  useEffect(() => {
    if (initRef.current) return;
    initRef.current = true;
    if (!getToken()) {
      router.push("/");
      return;
    }
    loadQueue();
  }, []);

  async function loadQueue() {
    setLoading(true);
    try {
      const r = await fetch(`${API}/api/learn/review-queue?limit=50`, {
        headers: { Authorization: `Bearer ${getToken()}` },
      });
      if (!r.ok) throw new Error(`HTTP ${r.status}`);
      const d = await r.json();
      const items = d.items || [];
      setQueue(items);
      if (items.length > 0) {
        await loadQuestion(items[0].question_id);
      }
    } catch (e: any) {
      console.error("queue load failed:", e);
    }
    setLoading(false);
  }

  async function loadQuestion(qid: string) {
    try {
      const r = await fetch(`${API}/api/learn/questions/${encodeURIComponent(qid)}`, {
        headers: { Authorization: `Bearer ${getToken()}` },
      });
      if (!r.ok) throw new Error(`HTTP ${r.status}`);
      const d = await r.json();
      setCurrent(d);
      setUserAnswer("");
      setShowHint(false);
      setStartTime(Date.now());
    } catch (e: any) {
      console.error("question load failed:", e);
      setCurrent(null);
    }
  }

  async function submitSelfEval(score: number) {
    if (!current || submitting) return;
    setSubmitting(true);
    try {
      const duration = Math.floor((Date.now() - startTime) / 1000);
      await fetch(`${API}/api/learn/questions/${encodeURIComponent(current.id)}/answer`, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
          Authorization: `Bearer ${getToken()}`,
        },
        body: JSON.stringify({
          user_answer: userAnswer || "(未作答)",
          score,
          blind_spots: [],
          duration_sec: duration,
          source: "review",
        }),
      });
      setCompleted((c) => c + 1);
      // 下一题
      const remaining = queue.slice(1);
      setQueue(remaining);
      if (remaining.length > 0) {
        await loadQuestion(remaining[0].question_id);
      } else {
        setCurrent(null);
      }
    } catch (e: any) {
      console.error("submit failed:", e);
    }
    setSubmitting(false);
  }

  if (loading) {
    return (
      <div className="min-h-screen bg-gradient-to-br from-[#0a0a1a] via-[#0f0f2e] to-[#1a0a2e] text-white flex items-center justify-center">
        <div className="inline-block w-6 h-6 border-2 border-indigo-500 border-t-transparent rounded-full animate-spin mr-3" />
        加载复习队列…
      </div>
    );
  }

  if (queue.length === 0 || !current) {
    return (
      <div className="min-h-screen bg-gradient-to-br from-[#0a0a1a] via-[#0f0f2e] to-[#1a0a2e] text-white">
        <main className="max-w-3xl mx-auto px-6 py-12 text-center">
          <div className="text-6xl mb-4">🎉</div>
          <h1 className="text-2xl font-bold mb-2">复习完成！</h1>
          <p className="text-gray-400 mb-6">本轮完成 {completed} 题</p>
          <div className="flex gap-3 justify-center">
            <button
              onClick={() => router.push("/learn")}
              className="px-4 py-2 rounded-xl bg-gradient-to-r from-indigo-500 to-purple-500 text-sm font-medium"
            >
              继续学习 →
            </button>
            <button
              onClick={() => { setCompleted(0); loadQueue(); }}
              className="px-4 py-2 rounded-xl bg-white/[0.04] hover:bg-white/[0.08] text-sm"
            >
              重新加载
            </button>
          </div>
        </main>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gradient-to-br from-[#0a0a1a] via-[#0f0f2e] to-[#1a0a2e] text-white">
      <main className="max-w-3xl mx-auto px-6 py-8">
        {/* Progress */}
        <div className="flex items-center justify-between mb-6 text-sm text-gray-400">
          <span>复习进度</span>
          <span>{completed} / {completed + queue.length}</span>
        </div>
        <div className="h-1 bg-white/[0.04] rounded-full overflow-hidden mb-8">
          <div
            className="h-full bg-gradient-to-r from-indigo-500 to-purple-500 transition-all"
            style={{ width: `${(completed / (completed + queue.length)) * 100}%` }}
          />
        </div>

        {/* Question card */}
        <div className="gradient-card rounded-2xl p-6 mb-6">
          <div className="flex items-center gap-2 mb-3 text-xs">
            <span className="px-2 py-0.5 rounded bg-indigo-500/20 text-indigo-300">
              {current.topic}
            </span>
            {current.sub_topic && (
              <span className="px-2 py-0.5 rounded bg-white/[0.04] text-gray-400">
                {current.sub_topic}
              </span>
            )}
            <span className="text-amber-400">
              {"⭐".repeat(current.difficulty)}
              <span className="text-gray-600">{"⭐".repeat(5 - current.difficulty)}</span>
            </span>
          </div>
          <div className="text-base leading-relaxed text-gray-100 whitespace-pre-wrap">
            {current.question_text}
          </div>
        </div>

        {/* Answer input */}
        <div className="gradient-card rounded-2xl p-5 mb-4">
          <textarea
            value={userAnswer}
            onChange={(e) => setUserAnswer(e.target.value)}
            rows={6}
            placeholder="写下你的回答…"
            className="w-full bg-transparent border-0 outline-none resize-none text-sm text-white placeholder-gray-500"
          />
          <div className="flex justify-between items-center mt-2 pt-2 border-t border-white/[0.04]">
            <button
              onClick={() => setShowHint(!showHint)}
              className="text-xs text-gray-400 hover:text-indigo-300"
            >
              {showHint ? "隐藏提示" : "💡 看提示"}
            </button>
            <span className="text-xs text-gray-500">{userAnswer.length} 字</span>
          </div>
          {showHint && current.answer_key_points?.length > 0 && (
            <div className="mt-3 p-3 bg-amber-500/[0.06] border border-amber-500/20 rounded-lg text-xs text-amber-200">
              <div className="font-medium mb-1">要点：</div>
              <ul className="list-disc list-inside space-y-1">
                {current.answer_key_points.map((p, i) => <li key={i}>{p}</li>)}
              </ul>
            </div>
          )}
        </div>

        {/* Self-eval buttons */}
        <div className="grid grid-cols-6 gap-2">
          {[
            { score: 0, label: "完全不会", color: "from-red-600 to-red-700" },
            { score: 1, label: "模糊", color: "from-orange-600 to-orange-700" },
            { score: 2, label: "差", color: "from-amber-600 to-amber-700" },
            { score: 3, label: "及格", color: "from-yellow-600 to-yellow-700" },
            { score: 4, label: "良好", color: "from-emerald-600 to-emerald-700" },
            { score: 5, label: "完美", color: "from-green-500 to-emerald-500" },
          ].map((s) => (
            <button
              key={s.score}
              onClick={() => submitSelfEval(s.score)}
              disabled={submitting}
              className={`px-3 py-3 rounded-xl bg-gradient-to-r ${s.color} text-xs font-medium disabled:opacity-30 hover:opacity-90 transition-all`}
            >
              {s.label}
            </button>
          ))}
        </div>
        <p className="text-xs text-gray-500 text-center mt-3">
          自我评估 0-5 分 · 后端用 SM-2 算法重算下次复习时间
        </p>
      </main>
    </div>
  );
}