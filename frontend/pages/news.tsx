import { useEffect, useState } from "react";
import { useRouter } from "next/router";
import { getToken } from "@/lib/api";

const API = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

export default function News() {
  const router = useRouter();
  const [tab, setTab] = useState<"daily" | "weekly" | "stats" | "sources">("daily");
  const [dailies, setDailies] = useState<any[]>([]);
  const [weeklies, setWeeklies] = useState<any[]>([]);
  const [report, setReport] = useState<any>(null);
  const [stats, setStats] = useState<any>(null);
  const [sources, setSources] = useState<any[]>([]);

  const h = () => ({ Authorization: `Bearer ${getToken()}` });

  useEffect(() => {
    if (!getToken()) { router.push("/"); return; }
    fetch(`${API}/api/news/daily`, { headers: h() }).then(r => r.json()).then(setDailies).catch(() => {});
    fetch(`${API}/api/news/weekly`, { headers: h() }).then(r => r.json()).then(setWeeklies).catch(() => {});
    fetch(`${API}/api/news/stats?days=14`, { headers: h() }).then(r => r.json()).then(setStats).catch(() => {});
    fetch(`${API}/api/news/sources`, { headers: h() }).then(r => r.json()).then(setSources).catch(() => {});
  }, []);

  const openDaily = (date: string) => {
    fetch(`${API}/api/news/daily/latest?date=${date}`, { headers: h() }).then(r => r.json()).then(setReport).catch(() => {});
  };
  const openWeekly = (week: string) => {
    fetch(`${API}/api/news/weekly/latest?week=${week}`, { headers: h() }).then(r => r.json()).then(setReport).catch(() => {});
  };

  const summary = stats?.summary || {};

  return (
    <div className="min-h-screen bg-[#050914] text-[#f1f5f9]">
      <nav className="sticky top-0 z-50 flex items-center gap-4 px-6 py-3.5 bg-[#0c1024]/90 backdrop-blur-xl border-b border-indigo-500/10">
        <button onClick={() => router.push("/dashboard")} className="text-gray-400 hover:text-white text-sm">← 仪表盘</button>
        <span className="text-lg font-bold bg-gradient-to-r from-indigo-400 to-purple-400 bg-clip-text text-transparent">信息推送</span>
        <div className="flex gap-1 ml-4">
          {[{ k: "daily", v: "日报" }, { k: "weekly", v: "周报" }, { k: "stats", v: "统计" }, { k: "sources", v: "信源" }].map(t => (
            <button key={t.k} onClick={() => setTab(t.k as any)}
              className={`px-4 py-2 rounded-lg text-sm font-medium transition-all ${tab === t.k ? "bg-indigo-500/20 text-indigo-300" : "text-gray-400 hover:text-gray-200"}`}
            >{t.v}</button>
          ))}
        </div>
        <span className="ml-auto text-xs text-gray-500">{dailies.length} 篇日报 · {weeklies.length} 篇周报</span>
      </nav>

      <main className="max-w-5xl mx-auto px-6 py-8">
        {/* Daily Tab */}
        {tab === "daily" && (
          <div>
            <h2 className="text-xl font-bold mb-5">AI 日报</h2>
            {report ? (
              <div className="bg-white/[0.03] border border-indigo-500/10 rounded-2xl p-7">
                <div className="flex items-center justify-between mb-4"><h3 className="text-lg font-bold">{report.name}</h3><button onClick={() => setReport(null)} className="text-gray-500 hover:text-white text-sm">✕ 返回列表</button></div>
                <div className="text-sm text-gray-300 leading-relaxed max-h-[65vh] overflow-y-auto whitespace-pre-wrap">{report.content}</div>
              </div>
            ) : dailies.length === 0 ? (
              <div className="text-center py-20 text-gray-500">暂无日报<br /><span className="text-xs mt-2 block">运行 scripts/ai_news.py daily 生成第一篇日报</span></div>
            ) : (
              <div className="space-y-2">
                {dailies.map(d => (
                  <div key={d.date} onClick={() => openDaily(d.date)} className="bg-white/[0.03] border border-indigo-500/10 rounded-xl p-4 cursor-pointer hover:border-indigo-500/30 transition-all flex items-center justify-between">
                    <div><span className="font-medium">{d.name}</span><span className="text-xs text-gray-500 ml-3">{(d.size / 1024).toFixed(1)} KB</span></div>
                    <span className="text-xs text-indigo-400">查看 →</span>
                  </div>
                ))}
              </div>
            )}
          </div>
        )}

        {/* Weekly Tab */}
        {tab === "weekly" && (
          <div>
            <h2 className="text-xl font-bold mb-5">AI 周报</h2>
            {report ? (
              <div className="bg-white/[0.03] border border-indigo-500/10 rounded-2xl p-7">
                <div className="flex items-center justify-between mb-4"><h3 className="text-lg font-bold">{report.name}</h3><button onClick={() => setReport(null)} className="text-gray-500 hover:text-white text-sm">✕ 返回列表</button></div>
                <div className="text-sm text-gray-300 leading-relaxed max-h-[65vh] overflow-y-auto whitespace-pre-wrap">{report.content}</div>
              </div>
            ) : weeklies.length === 0 ? (
              <div className="text-center py-20 text-gray-500">暂无周报<br /><span className="text-xs mt-2 block">运行 scripts/ai_news.py weekly 生成第一篇周报</span></div>
            ) : (
              <div className="space-y-2">
                {weeklies.map(w => (
                  <div key={w.week} onClick={() => openWeekly(w.week)} className="bg-white/[0.03] border border-indigo-500/10 rounded-xl p-4 cursor-pointer hover:border-indigo-500/30 transition-all flex items-center justify-between">
                    <div><span className="font-medium">{w.name}</span><span className="text-xs text-gray-500 ml-3">{(w.size / 1024).toFixed(1)} KB</span></div>
                    <span className="text-xs text-indigo-400">查看 →</span>
                  </div>
                ))}
              </div>
            )}
          </div>
        )}

        {/* Stats Tab */}
        {tab === "stats" && stats && (
          <div>
            <h2 className="text-xl font-bold mb-5">代码统计</h2>
            <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mb-6">
              {[{ v: summary.total_days || 0, l: "活跃天数", c: "text-indigo-400" }, { v: (summary.total_tokens / 1000).toFixed(0) + "K", l: "总 Token", c: "text-amber-400" }, { v: (summary.total_code / 1000).toFixed(1) + "K", l: "代码行", c: "text-emerald-400" }, { v: summary.total_commits || 0, l: "Commits", c: "text-purple-400" }].map(s => (
                <div key={s.l} className="bg-white/[0.03] border border-indigo-500/10 rounded-2xl p-6 text-center">
                  <div className={`text-3xl font-bold font-mono ${s.c}`}>{s.v}</div><div className="text-xs text-gray-500 mt-1.5">{s.l}</div>
                </div>
              ))}
            </div>
            {stats.daily?.length > 0 && (
              <div className="bg-white/[0.03] border border-indigo-500/10 rounded-2xl p-7">
                <h3 className="text-base font-semibold mb-4">每日明细</h3>
                <div className="overflow-x-auto">
                  <table className="w-full text-sm">
                    <thead><tr className="text-gray-400 text-xs uppercase tracking-wider">
                      <th className="text-left py-2 px-3">日期</th><th className="text-right py-2 px-3">Token 入</th><th className="text-right py-2 px-3">Token 出</th><th className="text-right py-2 px-3">代码+</th><th className="text-right py-2 px-3">代码-</th><th className="text-right py-2 px-3">Commits</th>
                    </tr></thead>
                    <tbody>
                      {stats.daily.map((d: any) => (
                        <tr key={d.date} className="border-t border-indigo-500/5 hover:bg-white/[0.02] transition-colors">
                          <td className="py-2.5 px-3 font-mono text-xs">{d.date}</td>
                          <td className="py-2.5 px-3 text-right font-mono text-xs">{d.tokens_in?.toLocaleString()}</td>
                          <td className="py-2.5 px-3 text-right font-mono text-xs">{d.tokens_out?.toLocaleString()}</td>
                          <td className="py-2.5 px-3 text-right font-mono text-xs text-emerald-400">{d.code_added?.toLocaleString()}</td>
                          <td className="py-2.5 px-3 text-right font-mono text-xs text-red-400">{d.code_deleted?.toLocaleString()}</td>
                          <td className="py-2.5 px-3 text-right font-mono text-xs">{d.commits}</td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              </div>
            )}
            <div className="mt-2 text-xs text-gray-500">每天 23:07 自动采集 · 数据：~/.claude/projects/ + git log</div>
          </div>
        )}

        {/* Sources Tab */}
        {tab === "sources" && (
          <div>
            <h2 className="text-xl font-bold mb-5">信息来源</h2>
            <div className="space-y-3">
              {sources.map(s => (
                <div key={s.name} className="bg-white/[0.03] border border-indigo-500/10 rounded-xl p-4 flex items-center justify-between">
                  <div>
                    <div className="font-medium">{s.name}</div>
                    <div className="text-xs text-gray-500 mt-1">{s.url}</div>
                  </div>
                  <div className="flex items-center gap-3">
                    <span className={`px-2 py-1 rounded-full text-xs ${s.category === "大模型" ? "bg-indigo-500/10 text-indigo-300" : s.category === "应用" ? "bg-emerald-500/10 text-emerald-400" : "bg-amber-500/10 text-amber-400"}`}>{s.category}</span>
                    <span className={`w-2 h-2 rounded-full ${s.enabled ? "bg-emerald-400" : "bg-gray-600"}`} title={s.enabled ? "启用" : "禁用"} />
                  </div>
                </div>
              ))}
            </div>
            <div className="mt-4 p-4 bg-white/[0.02] rounded-xl text-xs text-gray-500">
              每天 8:03 生成日报 · 每周一 9:03 生成周报 · 生成后自动写入 Obsidian
            </div>
          </div>
        )}
      </main>
    </div>
  );
}
