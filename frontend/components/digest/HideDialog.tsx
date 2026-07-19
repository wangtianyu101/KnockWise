"use client";

import { useState } from "react";

const REASONS = [
  { value: "not_interested", label: "不感兴趣" },
  { value: "low_quality", label: "内容质量低" },
  { value: "already_seen", label: "已从其他渠道看过" },
] as const;

const KEYWORD_WHITELIST = /^[a-zA-Z0-9一-龥]+$/;

export function HideDialog({
  open,
  onOpenChange,
  onConfirm,
  itemTitle,
  suggestedTopics = [],
}: {
  open: boolean;
  onOpenChange: (open: boolean) => void;
  onConfirm: (reason: string, keywords: string[]) => void;
  itemTitle: string;
  suggestedTopics?: string[];
}) {
  const [reason, setReason] = useState<string>("not_interested");
  const [topics, setTopics] = useState<Set<string>>(new Set(suggestedTopics));
  const [customTopic, setCustomTopic] = useState("");

  const toggleTopic = (kw: string) => {
    const next = new Set(topics);
    if (next.has(kw)) next.delete(kw);
    else if (next.size < 5) next.add(kw);
    setTopics(next);
  };

  const addCustom = () => {
    const kw = customTopic.trim();
    if (!kw || !KEYWORD_WHITELIST.test(kw) || topics.size >= 5) return;
    toggleTopic(kw);
    setCustomTopic("");
  };

  if (!open) return null;
  return (
    <div
      className="fixed inset-0 bg-black/75 backdrop-blur-sm flex items-center justify-center z-50"
      onClick={() => onOpenChange(false)}
    >
      <div
        className="bg-[rgba(15,20,40,0.95)] backdrop-blur-2xl border border-[rgba(99,102,241,0.25)] rounded-2xl p-8 w-[520px] max-w-[90vw] max-h-[90vh] overflow-y-auto shadow-2xl"
        onClick={(e) => e.stopPropagation()}
      >
        <h2 className="text-xl font-bold mb-1">不再推送类似内容？</h2>
        <p className="text-[13px] text-[#94a3b8] mb-5">{itemTitle}</p>

        <div className="flex flex-col gap-2 mb-5">
          {REASONS.map((r) => (
            <label
              key={r.value}
              className={`flex items-center gap-2 p-3 rounded-lg cursor-pointer border ${
                reason === r.value
                  ? "bg-[rgba(99,102,241,0.08)] border-[rgba(99,102,241,0.5)]"
                  : "bg-[rgba(255,255,255,0.02)] border-[rgba(148,163,184,0.08)] hover:border-[rgba(99,102,241,0.25)]"
              }`}
            >
              <input
                type="radio"
                name="reason"
                value={r.value}
                checked={reason === r.value}
                onChange={() => setReason(r.value)}
              />
              <span className="text-sm">{r.label}</span>
            </label>
          ))}
        </div>

        <div className="mb-5">
          <p className="text-xs text-[#94a3b8] mb-2">关键词（点击屏蔽 · 最多 5 个）</p>
          <div className="flex flex-wrap gap-1.5 mb-2">
            {suggestedTopics.map((kw) => (
              <span
                key={kw}
                onClick={() => toggleTopic(kw)}
                className={`cursor-pointer px-2 py-0.5 rounded text-[11px] font-medium border ${
                  topics.has(kw)
                    ? "bg-[rgba(248,113,113,0.3)] text-white border-[rgba(248,113,113,0.5)]"
                    : "bg-[rgba(96,165,250,0.18)] text-[#93c5fd] border-[rgba(96,165,250,0.35)]"
                }`}
              >
                {kw}
              </span>
            ))}
          </div>
          <div className="flex gap-1">
            <input
              type="text"
              value={customTopic}
              onChange={(e) => setCustomTopic(e.target.value)}
              onKeyDown={(e) => e.key === "Enter" && addCustom()}
              placeholder="+ 自定义关键词"
              className="flex-1 bg-[rgba(15,20,40,0.7)] border border-[rgba(148,163,184,0.12)] rounded-md px-2 py-1 text-xs text-white placeholder:text-[#64748b] focus:outline-none focus:border-[rgba(99,102,241,0.5)]"
            />
          </div>
          <p className="text-[10px] text-[#64748b] mt-1.5">屏蔽后 7 天内同类内容权重 -50%</p>
        </div>

        <div className="flex justify-end gap-2 pt-4 border-t border-[rgba(148,163,184,0.08)]">
          <button
            onClick={() => onOpenChange(false)}
            className="px-4 py-2 rounded-md text-sm bg-transparent border border-[rgba(148,163,184,0.12)] text-[#94a3b8] hover:bg-[rgba(255,255,255,0.04)]"
          >
            取消
          </button>
          <button
            onClick={() => { onConfirm(reason, Array.from(topics)); onOpenChange(false); }}
            className="px-4 py-2 rounded-md text-sm bg-[rgba(248,113,113,0.15)] text-[#fca5a5] border border-[rgba(248,113,113,0.3)] hover:bg-[rgba(248,113,113,0.2)]"
          >
            确认屏蔽
          </button>
        </div>
      </div>
    </div>
  );
}
