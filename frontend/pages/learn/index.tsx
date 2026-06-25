/**
 * Learn — 学 tab (题库浏览)
 *
 * 路由: /learn
 * 功能: 题目列表 (topic/difficulty/bookmarked 过滤) + 分页 + 收藏切换 + 跳详情
 * 配套: docs/10-架构/面试题库-页面规划.md · 4.2 学 tab
 */

import React, { useEffect, useState, useCallback, useRef } from "react";
import { useRouter } from "next/router";
import { getToken } from "@/lib/api";
import QuestionRow from "@/components/learn/QuestionRow";
import MasteryBadge from "@/components/shared/MasteryBadge";
import type { QuestionListItem } from "@/types/learn";

const API = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";
const SEARCH_DEBOUNCE_MS = 300;

const TOPICS = [
  { value: "", label: "全部" },
  { value: "agent", label: "Agent" },
  { value: "rag", label: "RAG" },
  { value: "system_design", label: "系统设计" },
  { value: "llm", label: "LLM 基础" },
  { value: "backend", label: "后端工程" },
  { value: "frontend", label: "前端" },
];

const DIFFICULTIES = [
  { value: 0, label: "全部难度" },
  { value: 1, label: "⭐ 入门" },
  { value: 2, label: "⭐⭐ 简单" },
  { value: 3, label: "⭐⭐⭐ 中等" },
  { value: 4, label: "⭐⭐⭐⭐ 困难" },
  { value: 5, label: "⭐⭐⭐⭐⭐ 专家" },
];

export default function LearnPage() {
  const router = useRouter();
  const [questions, setQuestions] = useState<QuestionListItem[]>([]);
  const [total, setTotal] = useState(0);
  const [topic, setTopic] = useState("");
  const [difficulty, setDifficulty] = useState(0);
  const [bookmarkedOnly, setBookmarkedOnly] = useState(false);
  const [query, setQuery] = useState("");
  const [page, setPage] = useState(1);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const PAGE_SIZE = 20;

  // 防止 React StrictMode 双触发
  const initRef = useRef(false);
  useEffect(() => {
    if (initRef.current) return;
    initRef.current = true;
    if (!getToken()) {
      router.push("/");
      return;
    }
    fetchList();
  }, []);

  const fetchList = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      const params = new URLSearchParams();
      if (topic) params.set("topic", topic);
      if (difficulty) params.set("difficulty", String(difficulty));
      if (bookmarkedOnly) params.set("bookmarked", "true");
      if (query.trim()) params.set("q", query.trim());
      params.set("page", String(page));
      params.set("size", String(PAGE_SIZE));
      const r = await fetch(`${API}/api/learn/questions?${params.toString()}`, {
        headers: { Authorization: `Bearer ${getToken()}` },
      });
      if (!r.ok) throw new Error(`HTTP ${r.status}`);
      const d = await r.json();
      setQuestions(d.items || []);
      setTotal(d.total || 0);
    } catch (e: any) {
      setError(e.message || "加载失败");
    }
    setLoading(false);
  }, [topic, difficulty, bookmarkedOnly, query, page]);

  useEffect(() => {
    fetchList();
  }, [fetchList]);

  // 搜索防抖
  useEffect(() => {
    const t = setTimeout(() => {
      setPage(1);
      fetchList();
    }, SEARCH_DEBOUNCE_MS);
    return () => clearTimeout(t);
  }, [query]);

  const toggleBookmark = async (q: QuestionListItem) => {
    try {
      const newVal = !q.progress?.bookmarked;
      await fetch(`${API}/api/learn/progress/${q.id}`, {
        method: "PATCH",
        headers: {
          "Content-Type": "application/json",
          Authorization: `Bearer ${getToken()}`,
        },
        body: JSON.stringify({ bookmarked: newVal }),
      });
      // 乐观更新
      setQuestions((prev) =>
        prev.map((x) =>
          x.id === q.id
            ? { ...x, progress: x.progress ? { ...x.progress, bookmarked: newVal } : null }
            : x
        )
      );
    } catch (e) {
      console.error("bookmark toggle failed:", e);
    }
  };

  const totalPages = Math.ceil(total / PAGE_SIZE);

  return (
    <div className="min-h-screen bg-gradient-to-br from-[#0a0a1a] via-[#0f0f2e] to-[#1a0a2e] text-white">
      <main className="max-w-6xl mx-auto px-6 py-8">
        {/* Header */}
        <div className="mb-6">
          <h1 className="text-3xl font-bold bg-gradient-to-r from-indigo-400 to-purple-400 bg-clip-text text-transparent">
            学 — 题库
          </h1>
          <p className="text-sm text-gray-400 mt-1">
            种子题 + 用户自建题 · 共 {total} 道
          </p>
        </div>

        {/* Filter bar */}
        <div className="gradient-card rounded-2xl p-4 mb-6">
          <div className="flex flex-wrap gap-3 items-center">
            {/* Topic */}
            <div className="flex-1 min-w-[140px]">
              <label className="text-xs text-gray-400 block mb-1">主题</label>
              <select
                value={topic}
                onChange={(e) => { setTopic(e.target.value); setPage(1); }}
                className="w-full bg-white/[0.04] border border-gray-700/30 rounded-lg px-3 py-2 text-sm"
              >
                {TOPICS.map((t) => (
                  <option key={t.value} value={t.value}>{t.label}</option>
                ))}
              </select>
            </div>

            {/* Difficulty */}
            <div className="flex-1 min-w-[140px]">
              <label className="text-xs text-gray-400 block mb-1">难度</label>
              <select
                value={difficulty}
                onChange={(e) => { setDifficulty(Number(e.target.value)); setPage(1); }}
                className="w-full bg-white/[0.04] border border-gray-700/30 rounded-lg px-3 py-2 text-sm"
              >
                {DIFFICULTIES.map((d) => (
                  <option key={d.value} value={d.value}>{d.label}</option>
                ))}
              </select>
            </div>

            {/* Search */}
            <div className="flex-1 min-w-[200px]">
              <label className="text-xs text-gray-400 block mb-1">搜索</label>
              <input
                type="text"
                value={query}
                onChange={(e) => setQuery(e.target.value)}
                placeholder="关键词…"
                className="w-full bg-white/[0.04] border border-gray-700/30 rounded-lg px-3 py-2 text-sm"
              />
            </div>

            {/* Bookmark toggle */}
            <label className="flex items-center gap-2 cursor-pointer mt-5">
              <input
                type="checkbox"
                checked={bookmarkedOnly}
                onChange={(e) => { setBookmarkedOnly(e.target.checked); setPage(1); }}
                className="rounded border-gray-700"
              />
              <span className="text-sm">只看收藏</span>
            </label>
          </div>
        </div>

        {/* List */}
        {loading ? (
          <div className="text-center text-gray-400 py-12">
            <div className="inline-block w-6 h-6 border-2 border-indigo-500 border-t-transparent rounded-full animate-spin mr-2" />
            加载中…
          </div>
        ) : error ? (
          <div className="gradient-card rounded-2xl p-6 text-center text-red-300">
            ❌ {error}
          </div>
        ) : questions.length === 0 ? (
          <div className="gradient-card rounded-2xl p-12 text-center text-gray-400">
            <div className="text-4xl mb-3">📭</div>
            <div>没有匹配的题目</div>
          </div>
        ) : (
          <>
            <div className="space-y-2">
              {questions.map((q) => (
                <QuestionRow
                  key={q.id}
                  question={q}
                  href={`/learn/${encodeURIComponent(q.id)}`}
                  onToggleBookmark={toggleBookmark}
                />
              ))}
            </div>

            {/* Pagination */}
            {totalPages > 1 && (
              <div className="flex items-center justify-center gap-2 mt-6">
                <button
                  onClick={() => setPage(Math.max(1, page - 1))}
                  disabled={page === 1}
                  className="px-3 py-1.5 rounded-lg bg-white/[0.04] hover:bg-white/[0.08] text-sm disabled:opacity-30"
                >
                  ←
                </button>
                <span className="text-sm text-gray-400">
                  {page} / {totalPages}
                </span>
                <button
                  onClick={() => setPage(Math.min(totalPages, page + 1))}
                  disabled={page === totalPages}
                  className="px-3 py-1.5 rounded-lg bg-white/[0.04] hover:bg-white/[0.08] text-sm disabled:opacity-30"
                >
                  →
                </button>
              </div>
            )}
          </>
        )}
      </main>
    </div>
  );
}