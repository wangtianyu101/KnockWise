import { useEffect, useState, useRef } from "react";
import { useRouter } from "next/router";
import { getToken, clearToken } from "@/lib/api";

const API = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

type Filter = "all" | "completed" | "in_progress" | "favorites";

interface Interview {
  id: string;
  round: string;
  style: string;
  status: string;
  total_questions: number;
  overall_score: number | null;
  is_favorite?: boolean;
  started_at: string;
  ended_at: string | null;
}

const SEARCH_DEBOUNCE_MS = 300;

export default function InterviewHistory() {
  const router = useRouter();
  const [interviews, setInterviews] = useState<Interview[]>([]);
  const [filter, setFilter] = useState<Filter>("all");
  const [query, setQuery] = useState("");
  const [loading, setLoading] = useState(true);

  // Per-row pending action so we can show a spinner on the right button
  const [pendingId, setPendingId] = useState<string | null>(null);

  // The "in-flight" q value (what the server knows about). query is the
  // input's instantaneous value; we debounce 300ms before refetching.
  const debounceRef = useRef<NodeJS.Timeout | null>(null);
  const lastFetchedQ = useRef("");

  useEffect(() => {
    if (!getToken()) { router.push("/"); return; }
    // Initial load — no debounce
    fetchList("");
  }, [router]);

  // Debounced refetch when the search box changes
  useEffect(() => {
    if (query === lastFetchedQ.current) return;
    if (debounceRef.current) clearTimeout(debounceRef.current);
    debounceRef.current = setTimeout(() => {
      fetchList(query);
    }, SEARCH_DEBOUNCE_MS);
    return () => {
      if (debounceRef.current) clearTimeout(debounceRef.current);
    };
  }, [query]);

  async function fetchList(q: string) {
    setLoading(true);
    lastFetchedQ.current = q;
    try {
      const params = new URLSearchParams({ size: "50" });
      if (q.trim()) params.set("q", q.trim());
      const r = await fetch(`${API}/api/interviews?${params.toString()}`, {
        headers: { Authorization: `Bearer ${getToken()}` },
      });
      const d = await r.json();
      setInterviews(d.items || []);
    } catch (e) {
      console.error("fetch interviews failed:", e);
    }
    setLoading(false);
  }

  async function toggleFavorite(e: React.MouseEvent, iv: Interview) {
    e.stopPropagation();
    e.preventDefault();
    setPendingId(iv.id);
    try {
      const r = await fetch(`${API}/api/interviews/${iv.id}/favorite`, {
        method: "POST",
        headers: { Authorization: `Bearer ${getToken()}` },
      });
      if (!r.ok) {
        console.error("favorite failed:", r.status, await r.text());
        return;
      }
      const { is_favorite } = await r.json();
      setInterviews((prev) =>
        prev.map((x) => (x.id === iv.id ? { ...x, is_favorite } : x))
      );
      // If we're filtering by favorites and we just un-favorited, refetch so
      // the row disappears (cheaper than building a custom filter client-side).
      if (filter === "favorites" && !is_favorite) {
        await fetchList(query);
      }
    } finally {
      setPendingId(null);
    }
  }

  async function deleteInterview(e: React.MouseEvent, iv: Interview) {
    e.stopPropagation();
    e.preventDefault();
    if (!confirm(`确定要删除「${iv.round === "round2" ? "二轮" : "一轮"}面试」吗？此操作不可撤销。`)) {
      return;
    }
    setPendingId(iv.id);
    try {
      const r = await fetch(`${API}/api/interviews/${iv.id}`, {
        method: "DELETE",
        headers: { Authorization: `Bearer ${getToken()}` },
      });
      if (!r.ok) {
        console.error("delete failed:", r.status, await r.text());
        return;
      }
      setInterviews((prev) => prev.filter((x) => x.id !== iv.id));
    } finally {
      setPendingId(null);
    }
  }

  // Client-side filter on top of the server-side search — narrows by status
  // / favorite. (Server already applied ?q= and ?favorites=true when those
  // are set; this is a belt-and-suspenders pass that keeps the UI responsive
  // when toggling status tabs without refetching.)
  const filtered = filter === "all"
    ? interviews
    : filter === "favorites"
      ? interviews.filter((i) => i.is_favorite)
      : interviews.filter((i) => i.status === filter);

  const scoreColor = (s: number) =>
    s >= 4 ? "text-emerald-400" : s >= 3 ? "text-amber-400" : "text-red-400";
  const scoreStars = (s: number) =>
    s >= 4.5 ? "★★★★★" : s >= 3.5 ? "★★★★☆" : s >= 2.5 ? "★★★☆☆" : s >= 1.5 ? "★★☆☆☆" : "★☆☆☆☆";

  const FILTER_TABS: { k: Filter; v: string }[] = [
    { k: "all", v: "全部" },
    { k: "completed", v: "已完成" },
    { k: "in_progress", v: "进行中" },
    { k: "favorites", v: "已收藏" },
  ];

  return (
    <div className="min-h-screen bg-[#050914] text-[#f1f5f9]">
      <nav className="sticky top-0 z-50 flex items-center gap-4 px-6 py-3.5 bg-[#0c1024]/90 backdrop-blur-xl border-b border-indigo-500/10">
        <button onClick={() => router.push("/dashboard")} className="text-gray-400 hover:text-white text-sm">← 仪表盘</button>
        <span className="text-lg font-bold bg-gradient-to-r from-indigo-400 to-purple-400 bg-clip-text text-transparent">面试练习</span>
        <div className="flex gap-1 ml-4">
          {[
            { label: "个人信息", href: "/interview/profile" },
            { label: "面试记录", href: "/interview/history", active: true },
            { label: "能力分析", href: "/interview/analytics" },
          ].map(t => (
            <button key={t.href} onClick={() => router.push(t.href)}
              className={`px-4 py-2 rounded-lg text-sm font-medium transition-all ${(t as any).active ? "bg-indigo-500/20 text-indigo-300" : "text-gray-400 hover:text-gray-200"}`}
            >{t.label}</button>
          ))}
        </div>
        <div className="flex-1" />
        <button onClick={() => router.push("/interview/setup")} className="px-5 py-2.5 rounded-xl font-medium text-sm bg-gradient-to-r from-indigo-500 to-purple-500 text-white shadow-lg shadow-purple-500/20 hover:opacity-90 transition-all">
          新面试
        </button>
      </nav>

      <main className="max-w-4xl mx-auto px-6 py-10">
        <h2 className="text-2xl font-bold mb-6">面试记录</h2>

        {/* Filter row: tabs + search input. Stacks on narrow screens. */}
        <div className="flex flex-wrap items-center gap-3 mb-6">
          <div className="flex gap-2 flex-wrap">
            {FILTER_TABS.map(f => (
              <button key={f.k} onClick={() => setFilter(f.k)}
                className={`px-4 py-2 rounded-full text-xs font-medium border transition-all ${filter === f.k ? "bg-indigo-500/20 text-indigo-300 border-indigo-500/30" : "bg-white/[0.02] text-gray-400 border-gray-700/20 hover:border-indigo-500/20"}`}
              >{f.v}</button>
            ))}
          </div>

          <div className="flex-1 min-w-[200px] relative">
            <span className="absolute left-3 top-1/2 -translate-y-1/2 text-gray-500 text-sm pointer-events-none">🔍</span>
            <input
              type="text"
              value={query}
              onChange={(e) => setQuery(e.target.value)}
              placeholder="搜索问题、回答、轮次…"
              className="w-full pl-9 pr-9 py-2 rounded-full text-sm bg-white/[0.02] border border-gray-700/20 text-gray-200 placeholder-gray-500 focus:outline-none focus:border-indigo-500/40 focus:bg-white/[0.04] transition-all"
            />
            {query && (
              <button
                onClick={() => setQuery("")}
                title="清空"
                className="absolute right-3 top-1/2 -translate-y-1/2 text-gray-500 hover:text-gray-200 text-sm w-5 h-5 flex items-center justify-center"
              >
                ×
              </button>
            )}
          </div>
        </div>

        {loading ? <div className="text-gray-400 text-center py-20">加载中...</div> : filtered.length === 0 ? (
          <div className="text-center py-20 text-gray-500">
            <div className="text-4xl mb-4">
              {query ? "🔍" : filter === "favorites" ? "⭐" : "🎯"}
            </div>
            <p>
              {query
                ? <>没有匹配 <span className="text-gray-300">「{query}」</span> 的面试</>
                : filter === "favorites"
                  ? "还没有收藏的面试"
                  : "还没有面试记录"}
            </p>
            {query ? (
              <button onClick={() => setQuery("")}
                className="mt-4 px-6 py-2.5 rounded-xl bg-indigo-500/20 text-indigo-300 border border-indigo-500/30 hover:bg-indigo-500/30 transition-all text-sm">
                清空搜索
              </button>
            ) : (
              <button onClick={() => router.push("/interview/setup")} className="mt-4 px-6 py-2.5 rounded-xl bg-indigo-500/20 text-indigo-300 border border-indigo-500/30 hover:bg-indigo-500/30 transition-all text-sm">开始第一次面试</button>
            )}
          </div>
        ) : (
          <div className="space-y-3">
            {filtered.map(iv => (
              <div key={iv.id} onClick={() => router.push(`/interview/report?id=${iv.id}`)}
                className="bg-white/[0.03] backdrop-blur-xl border border-indigo-500/10 rounded-2xl p-5 flex items-center justify-between cursor-pointer hover:border-indigo-500/30 transition-all group"
              >
                <div className="flex items-center gap-5 flex-1 min-w-0">
                  <span className="text-xs text-gray-500 font-mono min-w-[80px]">{iv.started_at?.slice(0, 10) || "-"}</span>
                  <div className="min-w-0">
                    <div className="font-medium truncate">{iv.round === "round2" ? "二轮" : "一轮"}面试 · {iv.style === "standard" ? "标准" : iv.style}</div>
                    <div className="text-xs text-gray-500 mt-1">{iv.total_questions || 0} 题 · 状态: {iv.status === "completed" ? "已完成" : "进行中"}</div>
                  </div>
                </div>

                <div className="flex items-center gap-3 shrink-0">
                  {iv.overall_score != null && (
                    <div className="text-center">
                      <div className={`text-2xl font-bold font-mono ${scoreColor(iv.overall_score)}`}>{iv.overall_score}</div>
                      <div className={`text-xs ${scoreColor(iv.overall_score)}`}>{scoreStars(iv.overall_score)}</div>
                    </div>
                  )}

                  {/* Action buttons — stop propagation so row click doesn't navigate */}
                  <button
                    onClick={(e) => toggleFavorite(e, iv)}
                    disabled={pendingId === iv.id}
                    title={iv.is_favorite ? "取消收藏" : "收藏"}
                    className={`w-9 h-9 rounded-lg flex items-center justify-center text-lg transition-all ${
                      iv.is_favorite
                        ? "text-amber-400 hover:bg-amber-500/10"
                        : "text-gray-500 hover:text-amber-400 hover:bg-amber-500/5"
                    }`}
                  >
                    {iv.is_favorite ? "★" : "☆"}
                  </button>
                  <button
                    onClick={(e) => deleteInterview(e, iv)}
                    disabled={pendingId === iv.id}
                    title="删除"
                    className="w-9 h-9 rounded-lg flex items-center justify-center text-gray-500 hover:text-red-400 hover:bg-red-500/10 transition-all"
                  >
                    🗑
                  </button>

                  <span className="text-xs text-indigo-400 group-hover:translate-x-1 transition-transform">查看 →</span>
                </div>
              </div>
            ))}
          </div>
        )}
      </main>
    </div>
  );
}
