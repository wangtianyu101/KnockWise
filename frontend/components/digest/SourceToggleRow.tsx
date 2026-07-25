"use client";

import { useState } from "react";

interface DigestSourceItem {
  id: string;
  user_id?: string | null;
  name: string;
  url: string;
  category: string;
  type: "model" | "application";
  region: "domestic" | "overseas";
  enabled: boolean;
  is_default: boolean;
  last_fetched_at?: string | null;
  last_item_count: number;
  last_error?: string | null;
}

interface SourceToggleRowProps {
  source: DigestSourceItem;
  isDefault: boolean;
  enabled: boolean;
  onToggle: (sourceId: string, enabled: boolean) => void;
  onDelete?: (sourceId: string) => void;
}

function formatRelative(iso: string | null): string {
  if (!iso) return "未抓取";
  const ts = new Date(iso).getTime();
  if (Number.isNaN(ts)) return "未抓取";
  const diffSec = Math.max(0, Math.floor((Date.now() - ts) / 1000));
  if (diffSec < 3600) return `${Math.max(1, Math.floor(diffSec / 60))} 分钟前`;
  if (diffSec < 86400) return `${Math.floor(diffSec / 3600)} 小时前`;
  return `${Math.floor(diffSec / 86400)} 天前`;
}

export function SourceToggleRow({ source, isDefault, enabled, onToggle, onDelete }: SourceToggleRowProps) {
  const isOverseas = source.region === "overseas";
  const iconColor = isOverseas ? "rgba(52,211,153,0.15)" : "rgba(245,158,11,0.15)";
  const iconBorder = isOverseas ? "rgba(52,211,153,0.3)" : "rgba(245,158,11,0.3)";
  const [menuOpen, setMenuOpen] = useState(false);

  return (
    <div className="flex items-center gap-3 p-3.5 bg-[rgba(15,20,40,0.7)] backdrop-blur-xl border border-[rgba(148,163,184,0.08)] rounded-[10px] mb-2 transition-all hover:border-[rgba(99,102,241,0.25)] relative">
      <div
        className="w-9 h-9 rounded-lg flex items-center justify-center text-[18px] flex-shrink-0"
        style={{ background: iconColor, border: `1px solid ${iconBorder}` }}
        data-testid="source-icon"
      >
        {source.is_default ? "🤖" : "📡"}
      </div>
      <div className="flex-1 min-w-0">
        <div className="text-sm font-semibold mb-1">{source.name}</div>
        <div className="text-xs truncate text-[#64748b]">{source.url}</div>
        <div className="flex items-center gap-1 mt-1.5 text-[10px] flex-wrap">
          <span className={`px-1.5 py-0.5 rounded font-semibold border ${
            source.region === "overseas"
              ? "bg-[rgba(52,211,153,0.18)] text-[#6ee7b7] border-[rgba(52,211,153,0.35)]"
              : "bg-[rgba(245,158,11,0.18)] text-[#fcd34d] border-[rgba(245,158,11,0.35)]"
          }`}>{isOverseas ? "国外" : "国内"}</span>
          <span className={`px-1.5 py-0.5 rounded font-semibold border ${
            source.type === "model"
              ? "bg-[rgba(96,165,250,0.18)] text-[#93c5fd] border-[rgba(96,165,250,0.35)]"
              : "bg-[rgba(167,139,250,0.18)] text-[#c4b5fd] border-[rgba(167,139,250,0.35)]"
          }`}>{source.type === "model" ? "模型" : "应用"}</span>
          <span className={`px-1.5 py-0.5 rounded font-semibold border ${
            isDefault
              ? "bg-[rgba(52,211,153,0.15)] text-[#6ee7b7] border-[rgba(52,211,153,0.3)]"
              : "bg-[rgba(245,158,11,0.15)] text-[#fcd34d] border-[rgba(245,158,11,0.3)]"
          }`}>{isDefault ? "系统" : "自定义"}</span>
          <span className="text-[#64748b]">· {formatRelative(source.last_fetched_at)} · {source.last_item_count} 条</span>
          {source.last_error && (
            <span className="text-[#fca5a5] ml-1" title={source.last_error}>⚠ 抓取失败</span>
          )}
        </div>
      </div>
      <button
        onClick={() => onToggle(source.id, !enabled)}
        className={`relative w-10 h-[22px] rounded-[11px] cursor-pointer transition-colors flex-shrink-0 ${
          enabled ? "bg-[#6366f1]" : "bg-[rgba(148,163,184,0.2)]"
        }`}
        aria-label="Toggle source"
        data-testid="btn-toggle"
      >
        <span
          className={`absolute top-[2px] w-[18px] h-[18px] bg-white rounded-full transition-transform ${
            enabled ? "translate-x-[18px]" : "translate-x-0"
          }`}
        />
      </button>
      {/* ··· 操作菜单（仅自定义源可编辑/删除） */}
      {!isDefault && onDelete && (
        <div className="relative">
          <button
            onClick={() => setMenuOpen((v) => !v)}
            className="px-2 py-1 text-[#94a3b8] hover:text-[#f8fafc] rounded hover:bg-[rgba(255,255,255,0.05)]"
            aria-label="Source actions"
            data-testid="btn-menu"
          >
            ···
          </button>
          {menuOpen && (
            <>
              <div className="fixed inset-0 z-10" onClick={() => setMenuOpen(false)} />
              <div
                className="absolute right-0 top-full mt-1 z-20 bg-[rgba(15,20,40,0.98)] border border-[rgba(148,163,184,0.12)] rounded-lg py-1 shadow-xl min-w-[140px]"
                data-testid="source-menu"
              >
                <button
                  onClick={() => {
                    const newName = window.prompt('重命名', source.name);
                    if (newName && newName !== source.name) {
                      // spec R5: rename 通过 PATCH /sources/{id}
                      window.alert(`(演示) 将重命名为: ${newName}`);
                    }
                    setMenuOpen(false);
                  }}
                  className="w-full text-left px-3 py-2 text-sm text-[#cbd5e1] hover:bg-[rgba(99,102,241,0.12)] hover:text-white"
                >
                  重命名
                </button>
                <button
                  onClick={() => {
                    if (window.confirm(`确定删除信源「${source.name}」？历史 digest 中的引用将无法跳转`)) {
                      onDelete(source.id);
                    }
                    setMenuOpen(false);
                  }}
                  className="w-full text-left px-3 py-2 text-sm text-[#fca5a5] hover:bg-[rgba(248,113,113,0.12)]"
                  data-testid="btn-delete"
                >
                  删除
                </button>
              </div>
            </>
          )}
        </div>
      )}
    </div>
  );
}
