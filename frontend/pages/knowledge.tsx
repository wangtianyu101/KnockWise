import { useEffect, useState } from "react";
import { useRouter } from "next/router";
import { getToken } from "@/lib/api";
import RecentSedimentsCard from "@/components/v2-settlement/RecentSedimentsCard";

const API = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

export default function Knowledge() {
  const router = useRouter();
  const [tab, setTab] = useState<"browse" | "graph" | "stats">("browse");
  const [searchQ, setSearchQ] = useState("");
  const [results, setResults] = useState<any[]>([]);
  const [files, setFiles] = useState<any[]>([]);
  const [note, setNote] = useState<any>(null);
  const [stats, setStats] = useState<any>(null);
  const [graphData, setGraphData] = useState<any>(null);

  const h = () => ({ Authorization: `Bearer ${getToken()}` });

  useEffect(() => {
    if (!getToken()) { router.push("/"); return; }
    fetch(`${API}/api/knowledge/browse`, { headers: h() }).then(r => r.json()).then(setFiles).catch(() => {});
    fetch(`${API}/api/knowledge/stats`, { headers: h() }).then(r => r.json()).then(setStats).catch(() => {});
  }, []);

  const doSearch = () => {
    if (!searchQ.trim()) return;
    fetch(`${API}/api/knowledge/search?q=${encodeURIComponent(searchQ)}&limit=20`, { headers: h() })
      .then(r => r.json()).then(setResults).catch(() => {});
  };

  const openNote = (path: string) => {
    fetch(`${API}/api/knowledge/note?path=${encodeURIComponent(path)}`, { headers: h() })
      .then(r => r.json()).then(setNote).catch(() => {});
  };

  const loadGraph = () => {
    setTab("graph");
    if (!graphData) fetch(`${API}/api/knowledge/graph`, { headers: h() }).then(r => r.json()).then(setGraphData).catch(() => {});
  };

  return (
    <div className="min-h-screen bg-[#050914] text-[#f1f5f9]">
      <nav className="sticky top-0 z-50 flex items-center gap-4 px-6 py-3.5 bg-[#0c1024]/90 backdrop-blur-xl border-b border-indigo-500/10">
        <button onClick={() => router.push("/dashboard")} className="text-gray-400 hover:text-white text-sm">← 仪表盘</button>
        <span className="text-lg font-bold bg-gradient-to-r from-indigo-400 to-purple-400 bg-clip-text text-transparent">知识管理</span>
        <div className="flex gap-1 ml-4">
          {[{ k: "browse", v: "浏览" }, { k: "graph", v: "图谱" }, { k: "stats", v: "统计" }].map(t => (
            <button key={t.k} onClick={() => { setTab(t.k as any); if (t.k === "graph") loadGraph(); }}
              className={`px-4 py-2 rounded-lg text-sm font-medium transition-all ${tab === t.k ? "bg-indigo-500/20 text-indigo-300" : "text-gray-400 hover:text-gray-200"}`}
            >{t.v}</button>
          ))}
        </div>
        {stats && <span className="ml-auto text-xs text-gray-500">📄 {stats.total_notes} 篇 · ✍️ {(stats.total_words / 1000).toFixed(0)}K 字</span>}
      </nav>

      <main className="max-w-6xl mx-auto px-6 py-8">
        <div className="flex gap-3 mb-6">
          <input className="flex-1 px-4 py-2.5 rounded-xl bg-white/[0.03] border border-indigo-500/10 text-white placeholder-gray-500 focus:border-indigo-500 focus:outline-none text-sm"
            placeholder="搜索笔记..." value={searchQ} onChange={e => setSearchQ(e.target.value)} onKeyDown={e => e.key === "Enter" && doSearch()} />
          <button onClick={doSearch} className="px-6 py-2.5 rounded-xl bg-indigo-500/20 text-indigo-300 border border-indigo-500/30 hover:bg-indigo-500/30 transition-all text-sm">搜索</button>
        </div>

        {results.length > 0 && (
          <div className="mb-6"><h3 className="text-sm text-gray-400 mb-3">搜索结果 ({results.length})</h3>
            <div className="space-y-2">{results.map(r => (
              <div key={r.path} onClick={() => openNote(r.path)} className="bg-white/[0.03] border border-indigo-500/10 rounded-xl p-4 cursor-pointer hover:border-indigo-500/30 transition-all">
                <div className="font-medium text-sm">{r.name}</div><div className="text-xs text-gray-500 mt-1.5">{r.snippet}</div>
              </div>))}
            </div>
          </div>
        )}

        {note && (
          <div className="mb-6 bg-white/[0.03] border border-indigo-500/10 rounded-2xl p-7">
            <div className="flex items-center justify-between mb-4"><h2 className="text-lg font-bold">{note.name}</h2><button onClick={() => setNote(null)} className="text-gray-500 hover:text-white text-sm">✕ 关闭</button></div>
            {note.frontmatter?.tags && <div className="flex gap-2 mb-4">{note.frontmatter.tags.map((t: string) => <span key={t} className="px-2 py-0.5 rounded-full bg-indigo-500/10 text-indigo-300 text-xs border border-indigo-500/20">{t}</span>)}</div>}
            <div className="text-sm text-gray-300 leading-relaxed max-h-[60vh] overflow-y-auto whitespace-pre-wrap">{note.content}</div>
            {note.links?.length > 0 && <div className="mt-4 pt-4 border-t border-indigo-500/10"><span className="text-xs text-gray-500">[[ 双链 ]]:</span> {note.links.slice(0, 10).map((l: string) => <span key={l} className="ml-2 px-2 py-0.5 rounded bg-indigo-500/10 text-indigo-300 text-xs">{l}</span>)}</div>}
          </div>
        )}

        {tab === "browse" && (
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-3">
            {files.map(f => (
              <div key={f.path} onClick={() => f.type === "file" ? openNote(f.path) : null}
                className={`bg-white/[0.03] border border-indigo-500/10 rounded-xl p-4 cursor-pointer hover:border-indigo-500/30 transition-all ${f.type === "directory" ? "border-dashed" : ""}`}>
                <span className="mr-2">{f.type === "directory" ? "📁" : "📄"}</span>
                <span className="font-medium text-sm">{f.name}</span>
                <div className="text-xs text-gray-500 mt-1 ml-7">{f.type === "directory" ? `${f.children_count} 篇` : f.modified?.slice(0, 10)}</div>
              </div>
            ))}
          </div>
        )}

        {tab === "graph" && (
          <div className="bg-white/[0.03] border border-indigo-500/10 rounded-2xl p-7 text-center">
            <h3 className="text-base font-semibold mb-4">知识图谱</h3>
            {graphData ? <div><SVGGraph nodes={graphData.nodes} edges={graphData.edges} /><div className="text-xs text-gray-500 mt-3">{graphData.stats.total_nodes} 节点 · {graphData.stats.total_edges} 条边</div></div> : <div className="text-gray-500 py-12">加载中...</div>}
          </div>
        )}

        {tab === "stats" && stats && (
          <div className="grid grid-cols-1 md:grid-cols-2 gap-5">
            <div className="bg-white/[0.03] border border-indigo-500/10 rounded-2xl p-7">
              <h3 className="text-base font-semibold mb-5">写作统计</h3>
              <div className="grid grid-cols-3 gap-4 mb-6">
                {[{ v: stats.total_notes, l: "笔记" }, { v: (stats.total_words / 1000).toFixed(1) + "K", l: "字数" }, { v: (stats.total_chars / 1000).toFixed(0) + "K", l: "字符" }].map(s => (
                  <div key={s.l} className="bg-white/[0.02] rounded-xl p-4 text-center"><div className="text-2xl font-bold font-mono text-indigo-400">{s.v}</div><div className="text-xs text-gray-500 mt-1">{s.l}</div></div>
                ))}
              </div>
            </div>
            <div className="bg-white/[0.03] border border-indigo-500/10 rounded-2xl p-7">
              <h3 className="text-base font-semibold mb-5">领域分布</h3>
              <div className="space-y-3">
                {Object.entries(stats.by_folder || {}).map(([k, v]: [string, any]) => (
                  <div key={k} className="flex items-center gap-3"><span className="text-sm text-gray-400 w-20 truncate">{k}</span>
                    <div className="flex-1 h-2 bg-white/[0.04] rounded-full overflow-hidden"><div className="h-full bg-indigo-500/60 rounded-full" style={{ width: `${Math.min((v.notes / stats.total_notes) * 100, 100)}%` }} /></div>
                    <span className="text-xs text-gray-500 w-14 text-right">{v.notes} 篇</span>
                  </div>
                ))}
              </div>
            </div>
          </div>
        )}

        {/* V2.3-T24: 最近学习沉淀卡（V2_ENABLED feature flag 控制） */}
        {tab === "stats" && stats && <RecentSedimentsCard />}
      </main>
    </div>
  );
}

function SVGGraph({ nodes, edges }: { nodes: any[]; edges: any[] }) {
  const cx = 340, cy = 240, r = 180;
  const positions: Record<number, {x: number; y: number}> = {};
  const groups = [...new Set(nodes.map((n: any) => n.group))];
  const groupAngles: Record<string, number> = {};
  groups.forEach((g, i) => { groupAngles[g as string] = (i / groups.length) * Math.PI * 2; });
  nodes.forEach((n: any) => { const ga = groupAngles[n.group] || 0; const scatter = (n.id % 7) * 25 - 60; positions[n.id] = { x: cx + Math.cos(ga) * (r + scatter), y: cy + Math.sin(ga) * (r + scatter) }; });
  const colors = ["#6366f1", "#22c55e", "#f59e0b", "#ef4444", "#8b5cf6", "#06b6d4", "#ec4899"];
  return (
    <svg viewBox="0 0 680 480" className="w-full max-w-3xl mx-auto">
      {edges.map((e: any, i: number) => { const s = positions[e.source], t = positions[e.target]; if (!s || !t) return null; return <line key={i} x1={s.x} y1={s.y} x2={t.x} y2={t.y} stroke="rgba(255,255,255,0.06)" strokeWidth="1" />; })}
      {nodes.map((n: any) => { const p = positions[n.id]; if (!p) return null; const gi = groups.indexOf(n.group); const c = colors[gi % colors.length]; return <g key={n.id}><circle cx={p.x} cy={p.y} r={n.size / 3} fill={c} opacity="0.7" /><text x={p.x} y={p.y - n.size / 3 - 4} textAnchor="middle" fill="#94a3b8" fontSize="9">{n.label}</text></g>; })}
    </svg>
  );
}
