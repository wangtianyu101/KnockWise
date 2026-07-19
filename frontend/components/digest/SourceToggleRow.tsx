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
}

interface SourceToggleRowProps {
  source: DigestSourceItem;
  isDefault: boolean;
  enabled: boolean;
  onToggle: (sourceId: string, enabled: boolean) => void;
}

export function SourceToggleRow({ source, isDefault, enabled, onToggle }: SourceToggleRowProps) {
  const isOverseas = source.region === "overseas";
  const iconColor = isOverseas ? "rgba(52,211,153,0.15)" : "rgba(245,158,11,0.15)";
  const iconBorder = isOverseas ? "rgba(52,211,153,0.3)" : "rgba(245,158,11,0.3)";

  return (
    <div className="flex items-center gap-3 p-3.5 bg-[rgba(15,20,40,0.7)] backdrop-blur-xl border border-[rgba(148,163,184,0.08)] rounded-[10px] mb-2 transition-all hover:border-[rgba(99,102,241,0.25)]">
      <div
        className="w-9 h-9 rounded-lg flex items-center justify-center text-[18px] flex-shrink-0"
        style={{ background: iconColor, border: `1px solid ${iconBorder}` }}
      >
        {source.is_default ? "🤖" : "📡"}
      </div>
      <div className="flex-1 min-w-0">
        <div className="text-sm font-semibold mb-1">{source.name}</div>
        <div className="text-xs truncate text-[#64748b]">{source.url}</div>
        <div className="flex items-center gap-1 mt-1.5 text-[10px]">
          <span className={`px-1.5 py-0.5 rounded font-semibold border ${
            source.region === "overseas"
              ? "bg-[rgba(52,211,153,0.18)] text-[#6ee7b7] border-[rgba(52,211,153,0.35)]"
              : "bg-[rgba(245,158,11,0.18)] text-[#fcd34d] border-[rgba(245,158,11,0.35)]"
          }`}>{source.region}</span>
          <span className={`px-1.5 py-0.5 rounded font-semibold border ${
            source.type === "model"
              ? "bg-[rgba(96,165,250,0.18)] text-[#93c5fd] border-[rgba(96,165,250,0.35)]"
              : "bg-[rgba(167,139,250,0.18)] text-[#c4b5fd] border-[rgba(167,139,250,0.35)]"
          }`}>{source.type}</span>
          <span className={`px-1.5 py-0.5 rounded font-semibold border ${
            isDefault
              ? "bg-[rgba(52,211,153,0.15)] text-[#6ee7b7] border-[rgba(52,211,153,0.3)]"
              : "bg-[rgba(245,158,11,0.15)] text-[#fcd34d] border-[rgba(245,158,11,0.3)]"
          }`}>{isDefault ? "系统" : "自定义"}</span>
          <span className="text-[#64748b]">· {source.last_fetched_at ? "3h 前" : "未抓取"} · {source.last_item_count} 条</span>
        </div>
      </div>
      <button
        onClick={() => onToggle(source.id, !enabled)}
        className={`relative w-10 h-[22px] rounded-[11px] cursor-pointer transition-colors flex-shrink-0 ${
          enabled ? "bg-[#6366f1]" : "bg-[rgba(148,163,184,0.2)]"
        }`}
        aria-label="Toggle source"
      >
        <span
          className={`absolute top-[2px] w-[18px] h-[18px] bg-white rounded-full transition-transform ${
            enabled ? "translate-x-[18px]" : "translate-x-0"
          }`}
        />
      </button>
    </div>
  );
}
