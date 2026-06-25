/**
 * QA — 问答 tab (LLM 1v1 模拟面试官)
 *
 * 路由: /qa
 * 功能: 选题目 → 跟 LLM 多轮对话
 * 配套: docs/10-架构/面试题库-页面规划.md · 4.2 问答 tab
 */

import React, { useEffect, useState, useRef, useCallback } from "react";
import { useRouter } from "next/router";
import { getToken } from "@/lib/api";
import type { QAMessage } from "@/types/learn";

const API = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

export default function QAPage() {
  const router = useRouter();
  const [questionId, setQuestionId] = useState("");
  const [sessionId, setSessionId] = useState<string | null>(null);
  const [messages, setMessages] = useState<QAMessage[]>([]);
  const [input, setInput] = useState("");
  const [sending, setSending] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const scrollRef = useRef<HTMLDivElement>(null);

  const initRef = useRef(false);
  useEffect(() => {
    if (initRef.current) return;
    initRef.current = true;
    if (!getToken()) {
      router.push("/");
      return;
    }
  }, []);

  // auto scroll
  useEffect(() => {
    if (scrollRef.current) {
      scrollRef.current.scrollTop = scrollRef.current.scrollHeight;
    }
  }, [messages]);

  async function startSession(qid: string) {
    if (!qid.trim()) return;
    setError(null);
    setSending(true);
    try {
      const r = await fetch(`${API}/api/learn/qa/chat`, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
          Authorization: `Bearer ${getToken()}`,
        },
        body: JSON.stringify({
          question_id: qid.trim(),
          session_id: null,
          message: "你好，请帮我深入分析这道题",
        }),
      });
      if (!r.ok) {
        const e = await r.json().catch(() => ({ detail: r.statusText }));
        throw new Error(e.detail || `HTTP ${r.status}`);
      }
      const d = await r.json();
      setQuestionId(qid);
      setSessionId(d.session_id);
      setMessages(d.messages || []);
    } catch (e: any) {
      setError(e.message || "启动 session 失败");
    }
    setSending(false);
  }

  async function send() {
    if (!input.trim() || !sessionId || sending) return;
    const userMsg = input.trim();
    setInput("");
    // 乐观加 user 消息 (匹配 backend 返回的 schema)
    setMessages((prev) => [...prev, {
      id: `local-${Date.now()}`,
      role: "user",
      content: userMsg,
      created_at: new Date().toISOString(),
    }]);
    setSending(true);
    setError(null);
    try {
      const r = await fetch(`${API}/api/learn/qa/chat`, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
          Authorization: `Bearer ${getToken()}`,
        },
        body: JSON.stringify({
          question_id: questionId,
          session_id: sessionId,
          message: userMsg,
        }),
      });
      if (!r.ok) {
        const e = await r.json().catch(() => ({ detail: r.statusText }));
        throw new Error(e.detail || `HTTP ${r.status}`);
      }
      const d = await r.json();
      setMessages(d.messages || []);
    } catch (e: any) {
      setError(e.message || "发送失败");
    }
    setSending(false);
  }

  const handleKeyDown = (e: React.KeyboardEvent) => {
    if (e.key === "Enter" && !e.shiftKey) {
      e.preventDefault();
      send();
    }
  };

  return (
    <div className="min-h-screen bg-gradient-to-br from-[#0a0a1a] via-[#0f0f2e] to-[#1a0a2e] text-white">
      <main className="max-w-4xl mx-auto px-6 py-8 flex flex-col h-screen">
        {/* Header */}
        <div className="mb-4">
          <h1 className="text-2xl font-bold bg-gradient-to-r from-indigo-400 to-purple-400 bg-clip-text text-transparent">
            问答 — LLM 1v1 模拟面试
          </h1>
          <p className="text-sm text-gray-400 mt-1">选一道题 · 让 LLM 当面试官深挖</p>
        </div>

        {/* Question picker (only when no session) */}
        {!sessionId ? (
          <div className="gradient-card rounded-2xl p-6 mt-12">
            <div className="text-sm text-gray-400 mb-3">输入题库题 ID 开始 (例如 agent_001)</div>
            <div className="flex gap-2">
              <input
                value={questionId}
                onChange={(e) => setQuestionId(e.target.value)}
                placeholder="agent_001"
                className="flex-1 bg-white/[0.04] border border-gray-700/30 rounded-lg px-3 py-2 text-sm"
                onKeyDown={(e) => e.key === "Enter" && startSession(questionId)}
              />
              <button
                onClick={() => startSession(questionId)}
                disabled={!questionId.trim() || sending}
                className="px-4 py-2 rounded-lg bg-gradient-to-r from-indigo-500 to-purple-500 text-sm font-medium disabled:opacity-30"
              >
                {sending ? "启动中…" : "开始 →"}
              </button>
            </div>
            <div className="text-xs text-gray-500 mt-3">
              💡 也可以先去 <a href="/learn" className="text-indigo-400 underline">/learn</a> 选题
            </div>
          </div>
        ) : (
          <>
            {/* Session header */}
            <div className="flex items-center justify-between mb-3">
              <div className="text-sm text-gray-400">
                题: <span className="text-indigo-300">{questionId}</span>
              </div>
              <button
                onClick={() => { setSessionId(null); setMessages([]); setQuestionId(""); }}
                className="text-xs text-gray-400 hover:text-red-300"
              >
                结束 session
              </button>
            </div>

            {/* Messages */}
            <div
              ref={scrollRef}
              className="flex-1 overflow-y-auto gradient-card rounded-2xl p-4 space-y-3 mb-4"
            >
              {messages.length === 0 && (
                <div className="text-center text-gray-500 py-12 text-sm">
                  暂无消息
                </div>
              )}
              {messages.map((m, i) => (
                <div
                  key={i}
                  className={`flex ${m.role === "user" ? "justify-end" : "justify-start"}`}
                >
                  <div
                    className={`max-w-[80%] rounded-2xl px-4 py-2.5 text-sm whitespace-pre-wrap ${
                      m.role === "user"
                        ? "bg-gradient-to-r from-indigo-500 to-purple-500 text-white"
                        : "bg-white/[0.04] border border-gray-700/30 text-gray-100"
                    }`}
                  >
                    <div className="text-xs opacity-60 mb-1">
                      {m.role === "user" ? "你" : "AI 面试官"}
                    </div>
                    {m.content}
                  </div>
                </div>
              ))}
              {sending && (
                <div className="flex justify-start">
                  <div className="bg-white/[0.04] border border-gray-700/30 rounded-2xl px-4 py-2.5">
                    <div className="flex gap-1">
                      <span className="w-2 h-2 bg-indigo-400 rounded-full animate-bounce" />
                      <span className="w-2 h-2 bg-indigo-400 rounded-full animate-bounce" style={{ animationDelay: "0.1s" }} />
                      <span className="w-2 h-2 bg-indigo-400 rounded-full animate-bounce" style={{ animationDelay: "0.2s" }} />
                    </div>
                  </div>
                </div>
              )}
            </div>

            {/* Error */}
            {error && (
              <div className="mb-2 p-2 rounded-lg bg-red-500/10 border border-red-500/20 text-red-300 text-xs">
                ❌ {error}
              </div>
            )}

            {/* Input */}
            <div className="gradient-card rounded-2xl p-3">
              <textarea
                value={input}
                onChange={(e) => setInput(e.target.value)}
                onKeyDown={handleKeyDown}
                rows={2}
                placeholder="输入问题… (Enter 发送, Shift+Enter 换行)"
                disabled={sending}
                className="w-full bg-transparent border-0 outline-none resize-none text-sm text-white placeholder-gray-500 disabled:opacity-50"
              />
              <div className="flex justify-end gap-2 mt-2">
                <button
                  onClick={send}
                  disabled={!input.trim() || sending}
                  className="px-4 py-1.5 rounded-lg bg-gradient-to-r from-indigo-500 to-purple-500 text-sm font-medium disabled:opacity-30"
                >
                  发送 →
                </button>
              </div>
            </div>
          </>
        )}
      </main>
    </div>
  );
}