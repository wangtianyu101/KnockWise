import { useEffect, useRef, useState } from "react";
import { useRouter } from "next/router";
import {
  getProfile,
  updateProfile,
  uploadResume,
  deleteResume,
  getToken,
} from "@/lib/api";
import SideDrawer from "@/components/SideDrawer";

type Filter = "all" | "completed" | "in_progress" | "favorites";

interface UploadResult {
  extracted: {
    tech_stack: string[];
    years_of_exp: number;
    current_level: "junior" | "mid" | "senior";
    skill_map: Record<string, number>;
    suggested_target_companies: string[];
  } | null;
  resume_text: string;
  page_count: number;
  is_scanned: boolean;
  file_name: string;
  file_size: number;
  warning: string | null;
}

type UploadState =
  | { kind: "idle" }
  | { kind: "uploading"; fileName: string }
  | { kind: "parsed"; result: UploadResult }
  | { kind: "error"; message: string };

const TARGET_COMPANIES = ["字节跳动", "阿里巴巴", "腾讯", "美团", "小红书", "拼多多"];

const ALL_TECHS = [
  "LangChain", "LangGraph", "RAG", "Python", "Java", "Spring Boot",
  "K8s", "Docker", "React", "Go", "TypeScript", "MCP",
];

const LEVEL_LABELS: Record<string, string> = {
  junior: "初级 (0-2年)",
  mid: "中级 (2-5年)",
  senior: "高级 (5年+)",
};

function fmtSize(bytes: number): string {
  if (bytes < 1024) return `${bytes} B`;
  if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(0)} KB`;
  return `${(bytes / 1024 / 1024).toFixed(1)} MB`;
}

export default function InterviewProfile() {
  const router = useRouter();
  const [profile, setProfile] = useState<any>(null);
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [upload, setUpload] = useState<UploadState>({ kind: "idle" });
  const fileInputRef = useRef<HTMLInputElement>(null);

  // Side-drawer state for viewing the uploaded PDF original.
  // We fetch the PDF as a blob and wrap it in an object URL so the
  // Authorization header can be sent (which an <iframe src=...> cannot do
  // on its own).
  const [drawerOpen, setDrawerOpen] = useState(false);
  const [pdfBlobUrl, setPdfBlobUrl] = useState<string | null>(null);
  const [pdfLoading, setPdfLoading] = useState(false);
  const [pdfError, setPdfError] = useState<string | null>(null);

  // Form state — always reflects the "saved" baseline + any pending edits.
  const [form, setForm] = useState({
    display_name: "",
    years_of_exp: 3,
    current_level: "mid",
    tech_stack: [] as string[],
    target_companies: [] as string[],
    skill_map: {} as Record<string, number>,
    resume_summary: null as string | null,
  });

  useEffect(() => {
    if (!getToken()) { router.push("/"); return; }
    getProfile().then((p) => {
      setProfile(p);
      setForm({
        display_name: p.display_name || "",
        years_of_exp: p.years_of_exp || 3,
        current_level: p.current_level || "mid",
        tech_stack: p.tech_stack || [],
        target_companies: p.target_companies || [],
        skill_map: p.skill_map || {},
        resume_summary: p.resume_summary || null,
      });
      setLoading(false);
    }).catch(() => setLoading(false));
  }, [router]);

  const toggle = <T,>(arr: T[], item: T): T[] =>
    arr.includes(item) ? arr.filter((x) => x !== item) : [...arr, item];

  // ── Save handler — persists basic info + (if pending) the parsed fields ──
  const save = async (withParsed?: UploadResult["extracted"]) => {
    setSaving(true);
    try {
      const payload: Record<string, any> = {
        tech_stack: form.tech_stack,
        years_of_exp: form.years_of_exp,
        current_level: form.current_level,
        target_companies: form.target_companies,
        skill_map: form.skill_map,
      };
      // If we have parsed text, send it as resume_text so it's stored
      // in resume_summary for the side-drawer later.
      if (upload.kind === "parsed" && upload.result.resume_text) {
        payload.resume_text = upload.result.resume_text;
      }
      if (withParsed) {
        payload.tech_stack = withParsed.tech_stack;
        payload.years_of_exp = withParsed.years_of_exp;
        payload.current_level = withParsed.current_level;
        payload.skill_map = withParsed.skill_map;
        payload.target_companies = [
          ...new Set([...form.target_companies, ...withParsed.suggested_target_companies]),
        ];
      }
      const updated = await updateProfile(payload);
      setProfile(updated);
      setForm((f) => ({
        ...f,
        tech_stack: updated.tech_stack || [],
        years_of_exp: updated.years_of_exp,
        current_level: updated.current_level,
        target_companies: updated.target_companies || [],
        skill_map: updated.skill_map || {},
      }));
      setUpload({ kind: "idle" });
      // Light success feedback
      const orig = document.title;
      document.title = "✓ 已保存";
      setTimeout(() => { document.title = orig; }, 1200);
    } catch (e: any) {
      alert("保存失败：" + (e.message || String(e)));
    } finally {
      setSaving(false);
    }
  };

  // ── Upload handlers ──
  const onPickFile = () => fileInputRef.current?.click();

  const onFileSelected = async (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (!file) return;
    // Reset so picking the same file again fires onChange
    e.target.value = "";

    setUpload({ kind: "uploading", fileName: file.name });
    try {
      const result = await uploadResume(file);
      setUpload({ kind: "parsed", result });

      // Auto-fill the form with extracted fields. User reviews in-place.
      if (result.extracted) {
        setForm((f) => ({
          ...f,
          tech_stack: result.extracted!.tech_stack,
          years_of_exp: result.extracted!.years_of_exp,
          current_level: result.extracted!.current_level,
          skill_map: result.extracted!.skill_map,
          target_companies: Array.from(
            new Set([...f.target_companies, ...result.extracted!.suggested_target_companies])
          ),
        }));
      }
    } catch (err: any) {
      setUpload({ kind: "error", message: err.message || "上传失败" });
    }
  };

  const onDeleteResume = async () => {
    if (!confirm("确定要删除已上传的简历吗？已保存的个人资料不会丢失。")) return;
    try {
      await deleteResume();
      setUpload({ kind: "idle" });
      // Reload profile to get cleared resume_summary / skill_map
      const p = await getProfile();
      setProfile(p);
      setForm((f) => ({
        ...f,
        skill_map: p.skill_map || {},
        resume_summary: p.resume_summary || null,
      }));
    } catch (e: any) {
      alert("删除失败：" + (e.message || String(e)));
    }
  };

  // ── Skill map is auto-applied from LLM extraction on save. We keep the
  //    field in form state for the Profile round-trip but expose no editor
  //    for it — the 1-5 rating UI was busywork without much value.

// ── PDF preview drawer ──
  async function openPdfDrawer() {
    setDrawerOpen(true);
    if (pdfBlobUrl) return;  // already fetched this session
    setPdfLoading(true);
    setPdfError(null);
    try {
      const res = await fetch(`${process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000"}/api/profile/resume/file`, {
        headers: { Authorization: `Bearer ${getToken()}` },
      });
      if (!res.ok) {
        const err = await res.json().catch(() => ({ detail: res.statusText }));
        throw new Error(err.detail || `HTTP ${res.status}`);
      }
      const blob = await res.blob();
      setPdfBlobUrl(URL.createObjectURL(blob));
    } catch (e: any) {
      setPdfError(e.message || "加载失败");
    } finally {
      setPdfLoading(false);
    }
  }

  function closePdfDrawer() {
    setDrawerOpen(false);
  }

  // Free the blob URL when the page unmounts
  useEffect(() => {
    return () => {
      if (pdfBlobUrl) URL.revokeObjectURL(pdfBlobUrl);
    };
  }, [pdfBlobUrl]);

  if (loading) {
    return (
      <div className="min-h-screen bg-[#050914] flex items-center justify-center">
        <div className="text-gray-400">加载中...</div>
      </div>
    );
  }

  // ── Render ──
  return (
    <div className="min-h-screen bg-[#050914] text-[#f1f5f9]">
      <nav className="sticky top-0 z-50 flex items-center gap-4 px-6 py-3.5 bg-[#0c1024]/90 backdrop-blur-xl border-b border-indigo-500/10">
        <button onClick={() => router.push("/dashboard")} className="text-gray-400 hover:text-white text-sm">← 仪表盘</button>
        <span className="text-lg font-bold bg-gradient-to-r from-indigo-400 to-purple-400 bg-clip-text text-transparent">面试练习</span>
        <div className="flex gap-1 ml-4">
          {[
            { label: "个人信息", href: "/interview/profile", active: true },
            { label: "面试记录", href: "/interview/history" },
            { label: "能力分析", href: "/interview/analytics" },
          ].map((t) => (
            <button key={t.href} onClick={() => router.push(t.href)}
              className={`px-4 py-2 rounded-lg text-sm font-medium transition-all ${t.active ? "bg-indigo-500/20 text-indigo-300" : "text-gray-400 hover:text-gray-200"}`}
            >{t.label}</button>
          ))}
        </div>
        <div className="flex-1" />
        <button onClick={() => router.push("/interview/setup")} className="px-5 py-2.5 rounded-xl font-medium text-sm bg-gradient-to-r from-indigo-500 to-purple-500 text-white shadow-lg shadow-purple-500/20 hover:opacity-90 transition-all">
          开始面试
        </button>
        <div className="w-8 h-8 rounded-full bg-gradient-to-br from-indigo-500 to-purple-500 flex items-center justify-center text-sm font-bold text-white">
          {form.display_name?.[0] || "?"}
        </div>
      </nav>

      <main className="max-w-5xl mx-auto px-6 py-10">
        <div className="grid grid-cols-1 md:grid-cols-2 gap-5">
          {/* Basic Info */}
          <div className="bg-white/[0.03] backdrop-blur-xl border border-indigo-500/10 rounded-2xl p-7">
            <h3 className="text-lg font-semibold mb-5">基本信息</h3>
            <div className="space-y-4">
              <div>
                <label className="block text-sm text-gray-400 mb-1.5">昵称</label>
                <input className="w-full px-4 py-2.5 rounded-xl bg-white/[0.03] border border-indigo-500/10 text-white focus:border-indigo-500 focus:outline-none"
                  value={form.display_name} onChange={(e) => setForm({ ...form, display_name: e.target.value })} />
              </div>
              <div>
                <label className="block text-sm text-gray-400 mb-1.5">经验年限</label>
                <input type="number" min={0} max={50}
                  className="w-full px-4 py-2.5 rounded-xl bg-white/[0.03] border border-indigo-500/10 text-white focus:border-indigo-500 focus:outline-none"
                  value={form.years_of_exp} onChange={(e) => setForm({ ...form, years_of_exp: +e.target.value })} />
              </div>
              <div>
                <label className="block text-sm text-gray-400 mb-1.5">当前级别</label>
                <select className="w-full px-4 py-2.5 rounded-xl bg-white/[0.03] border border-indigo-500/10 text-white focus:border-indigo-500 focus:outline-none"
                  value={form.current_level}
                  onChange={(e) => setForm({ ...form, current_level: e.target.value })}>
                  <option value="junior">{LEVEL_LABELS.junior}</option>
                  <option value="mid">{LEVEL_LABELS.mid}</option>
                  <option value="senior">{LEVEL_LABELS.senior}</option>
                </select>
              </div>
              <div>
                <label className="block text-sm text-gray-400 mb-1.5">目标公司</label>
                <div className="flex flex-wrap gap-2">
                  {TARGET_COMPANIES.map((c) => (
                    <button key={c} onClick={() => setForm({ ...form, target_companies: toggle(form.target_companies, c) })}
                      className={`px-3 py-1.5 rounded-full text-xs border transition-all ${form.target_companies.includes(c) ? "bg-indigo-500/20 text-indigo-300 border-indigo-500/30" : "bg-white/[0.02] text-gray-400 border-gray-700/20 hover:border-indigo-500/20"}`}
                    >{c}</button>
                  ))}
                </div>
              </div>
              <button onClick={() => save()} disabled={saving}
                className="w-full py-2.5 rounded-xl font-medium bg-gradient-to-r from-indigo-500 to-purple-500 text-white hover:opacity-90 transition-all disabled:opacity-50">
                {saving ? "保存中..." : "保存修改"}
              </button>
            </div>
          </div>

          {/* Skills & Resume */}
          <div className="bg-white/[0.03] backdrop-blur-xl border border-indigo-500/10 rounded-2xl p-7">
            <h3 className="text-lg font-semibold mb-5">技能栈 & 简历</h3>

            {/* ── Hidden file input ── */}
            <input
              ref={fileInputRef}
              type="file"
              accept="application/pdf,.pdf"
              className="hidden"
              onChange={onFileSelected}
            />

            {/* ── Upload area ── */}
            {upload.kind === "idle" && (
              <div
                onClick={onPickFile}
                className="border-2 border-dashed border-indigo-500/20 rounded-2xl p-8 text-center text-gray-400 text-sm cursor-pointer hover:border-indigo-500/40 hover:text-indigo-300 transition-all"
              >
                <div className="text-3xl mb-2">📄</div>
                点击或拖拽上传简历 PDF<br />
                <span className="text-xs text-gray-500">支持 PDF，最大 10MB，AI 自动解析</span>
              </div>
            )}

            {upload.kind === "uploading" && (
              <div className="border-2 border-indigo-500/30 rounded-2xl p-8 text-center bg-indigo-500/5">
                <div className="inline-block w-8 h-8 border-2 border-indigo-500 border-t-transparent rounded-full animate-spin mb-3" />
                <div className="text-sm text-indigo-300">正在解析 {upload.fileName}…</div>
                <div className="text-xs text-gray-500 mt-1">PDF 抽取 + AI 抽取字段，约 5-15 秒</div>
              </div>
            )}

            {upload.kind === "error" && (
              <div className="border-2 border-red-500/30 rounded-2xl p-5 bg-red-500/5">
                <div className="text-sm text-red-300 mb-2">❌ {upload.message}</div>
                <button onClick={onPickFile}
                  className="px-3 py-1.5 rounded-lg bg-white/[0.04] hover:bg-white/[0.08] text-xs text-gray-300">
                  重试
                </button>
              </div>
            )}

            {upload.kind === "parsed" && (
              <div className="space-y-4">
                {/* File metadata card — real data, not hardcoded */}
                <div className="p-3.5 bg-emerald-500/[0.06] border border-emerald-500/10 rounded-xl text-sm flex items-center gap-2">
                  <span className="text-emerald-400">📄</span>
                  <span className="truncate flex-1" title={upload.result.file_name}>{upload.result.file_name}</span>
                  <span className="text-xs text-gray-500 shrink-0 mr-2">
                    {fmtSize(upload.result.file_size)} · {upload.result.page_count} 页
                  </span>
                  <button
                    onClick={openPdfDrawer}
                    title="在侧边栏中预览原 PDF"
                    className="text-xs text-indigo-300 hover:text-indigo-200 border border-indigo-500/30 hover:border-indigo-500/50 px-2.5 py-1 rounded-md transition-all"
                  >
                    查看原文
                  </button>
                </div>

                {upload.result.warning && (
                  <div className="p-3 bg-amber-500/[0.08] border border-amber-500/20 rounded-xl text-xs text-amber-200">
                    ⚠ {upload.result.warning}
                  </div>
                )}

                {/* Editable skill chips — extracted from resume */}
                <div>
                  <div className="text-xs text-gray-400 mb-2">技术栈（点击切换 / 长按删除）</div>
                  <div className="flex flex-wrap gap-2">
                    {form.tech_stack.map((t) => (
                      <button key={t} onClick={() => setForm({ ...form, tech_stack: form.tech_stack.filter((x) => x !== t) })}
                        title="点击移除"
                        className="px-3 py-1.5 rounded-full text-xs bg-indigo-500/20 text-indigo-300 border border-indigo-500/30 hover:bg-red-500/20 hover:text-red-300 hover:border-red-500/30 transition-all">
                        ✓ {t} ×
                      </button>
                    ))}
                    {/* Quick-add chips for ALL_TECHS not yet selected */}
                    {ALL_TECHS.filter((t) => !form.tech_stack.includes(t)).map((t) => (
                      <button key={t} onClick={() => setForm({ ...form, tech_stack: [...form.tech_stack, t] })}
                        className="px-3 py-1.5 rounded-full text-xs bg-white/[0.02] text-gray-400 border border-gray-700/20 hover:border-indigo-500/20">
                        + {t}
                      </button>
                    ))}
                  </div>
                </div>

                <div className="flex gap-2 pt-2">
                  <button onClick={() => save()} disabled={saving}
                    className="flex-1 py-2.5 rounded-xl font-medium bg-gradient-to-r from-indigo-500 to-purple-500 text-white hover:opacity-90 transition-all disabled:opacity-50">
                    {saving ? "保存中..." : "✓ 保存到个人资料"}
                  </button>
                  <button onClick={onPickFile} title="重新上传"
                    className="px-4 py-2.5 rounded-xl bg-white/[0.04] hover:bg-white/[0.08] text-sm text-gray-300">
                    重新上传
                  </button>
                  {form.resume_summary && (
                    <button onClick={onDeleteResume} title="删除简历"
                      className="px-3 py-2.5 rounded-xl bg-white/[0.04] hover:bg-red-500/10 hover:text-red-400 text-sm text-gray-400">
                      🗑
                    </button>
                  )}
                </div>
              </div>
            )}
          </div>
        </div>
      </main>

      {/* ── Resume PDF side-drawer ── */}
      <SideDrawer
        open={drawerOpen}
        onClose={closePdfDrawer}
        title="简历原文"
        width="w-[640px]"
      >
        <div className="h-full flex flex-col">
          {pdfLoading && (
            <div className="flex-1 flex items-center justify-center text-gray-400 text-sm">
              <div className="inline-block w-6 h-6 border-2 border-indigo-500 border-t-transparent rounded-full animate-spin mr-3" />
              加载 PDF…
            </div>
          )}
          {pdfError && (
            <div className="flex-1 flex items-center justify-center text-red-300 text-sm p-6 text-center">
              ❌ {pdfError}
            </div>
          )}
          {pdfBlobUrl && !pdfLoading && !pdfError && (
            <>
              <div className="px-5 py-2 border-b border-indigo-500/10 flex items-center justify-between text-xs text-gray-400 shrink-0">
                <span>PDF 预览</span>
                <a
                  href={pdfBlobUrl}
                  download={upload.kind === "parsed" ? upload.result.file_name : "resume.pdf"}
                  className="text-indigo-300 hover:text-indigo-200 underline"
                >
                  下载
                </a>
              </div>
              <iframe
                src={pdfBlobUrl}
                title="简历 PDF 预览"
                className="flex-1 w-full bg-gray-900"
              />
            </>
          )}
        </div>
      </SideDrawer>
    </div>
  );
}