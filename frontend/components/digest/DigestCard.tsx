"use client";

import { ExternalLink, Bookmark, BookmarkCheck, EyeOff } from "lucide-react";

/** Glassmorphism 容器 wrapper · 与 DigestCard 卡片样式统一 */
export function GlassCard({ children, className = "" }: { children: React.ReactNode; className?: string }) {
  return (
    <div className={`bg-[rgba(15,20,40,0.7)] backdrop-blur-xl border border-[rgba(148,163,184,0.08)] rounded-xl p-5 ${className}`}>
      {children}
    </div>
  );
}

interface DigestItem {
  id: string;
  rank: number;
  title: string;
  summary?: string;
  quality_score: number;
  type: "model" | "application";
  region: "domestic" | "overseas";
  category: string;
  source_name: string;
  source_url: string;
  published_at?: string;
  estimated_minutes: number;
  is_read?: boolean;
  is_bookmarked?: boolean;
}

interface DigestCardProps {
  item: DigestItem;
  onHide?: (itemId: string) => void;
  onBookmark?: (itemId: string) => void;
  onOpenDetail?: (itemId: string) => void;
}

const TYPE_COLORS: Record<"model" | "application", string> = {
  model: "bg-[rgba(96,165,250,0.18)] text-[#93c5fd] border-[rgba(96,165,250,0.35)]",
  application: "bg-[rgba(167,139,250,0.18)] text-[#c4b5fd] border-[rgba(167,139,250,0.35)]",
};
const REGION_COLORS: Record<"domestic" | "overseas", string> = {
  domestic: "bg-[rgba(245,158,11,0.18)] text-[#fcd34d] border-[rgba(245,158,11,0.35)]",
  overseas: "bg-[rgba(52,211,153,0.18)] text-[#6ee7b7] border-[rgba(52,211,153,0.35)]",
};

/**
 * 主题标签样式（mockup 01-today.html 第 3 个标签）
 * DB category 是 headline/paper/engineering/opinion/...
 * 颜色映射：头条(粉)/工程(蓝)/论文(紫)/观点(琥珀)
 */
const CATEGORY_LABELS: Record<string, { label: string; style: string }> = {
  headline: { label: "头条", style: "bg-[rgba(244,114,182,0.18)] text-[#fbcfe8] border-[rgba(244,114,182,0.35)]" },
  engineering: { label: "工程", style: "bg-[rgba(96,165,250,0.12)] text-[#93c5fd] border-[rgba(96,165,250,0.25)]" },
  paper: { label: "论文", style: "bg-[rgba(167,139,250,0.18)] text-[#c4b5fd] border-[rgba(167,139,250,0.35)]" },
  opinion: { label: "观点", style: "bg-[rgba(245,158,11,0.18)] text-[#fcd34d] border-[rgba(245,158,11,0.35)]" },
};

/** 中文标签映射（T1 · mockup 对齐） */
const TYPE_LABELS: Record<"model" | "application", string> = {
  model: "模型",
  application: "应用",
};
const REGION_LABELS: Record<"domestic" | "overseas", string> = {
  domestic: "国内",
  overseas: "国外",
};

export function DigestCard({ item, onHide, onBookmark, onOpenDetail }: DigestCardProps) {
  const categoryInfo = CATEGORY_LABELS[item.category] || {
    label: item.category,
    style: "bg-[rgba(148,163,184,0.06)] text-[#94a3b8] border-[rgba(148,163,184,0.08)]",
  };
  return (
    <article
      onClick={() => onOpenDetail?.(item.id)}
      className={`digest-card bg-[rgba(15,20,40,0.7)] backdrop-blur-xl border rounded-xl p-5 mb-3 transition-all hover:shadow-lg cursor-pointer ${
        item.is_read
          ? "opacity-60 border-[rgba(148,163,184,0.08)] border-l-[3px] border-l-[rgba(148,163,184,0.3)]"
          : "border-[rgba(148,163,184,0.08)] border-l-[3px] border-l-[rgba(99,102,241,0.6)] hover:border-[rgba(99,102,241,0.25)]"
      }`}
      data-testid="digest-card"
      data-rank={item.rank}
    >
      <div className="flex items-center gap-2 mb-3 text-xs text-[#94a3b8] flex-wrap">
        <span className={`px-2 py-0.5 rounded text-[11px] font-medium border ${TYPE_COLORS[item.type]}`}>
          {TYPE_LABELS[item.type]}
        </span>
        <span className={`px-2 py-0.5 rounded text-[11px] font-medium border ${REGION_COLORS[item.region]}`}>
          {REGION_LABELS[item.region]}
        </span>
        <span className={`px-2 py-0.5 rounded text-[11px] font-medium border ${categoryInfo.style}`}>
          {categoryInfo.label}
        </span>
        <span>· {item.source_name}</span>
      </div>
      <h2 className="text-xl font-bold mb-2 tracking-tight leading-tight">{item.title}</h2>
      {item.summary && (
        <p className="text-sm leading-relaxed text-[#94a3b8] mb-3">{item.summary}</p>
      )}
      <div className="flex items-center justify-between text-xs text-[#64748b]">
        <div className="flex items-center gap-3">
          <span>⏱ {item.estimated_minutes} 分钟</span>
          <span>·</span>
          <span className="text-[#f59e0b]">⭐ {item.quality_score}</span>
        </div>
        <div className="flex items-center gap-2">
          <a
            href={item.source_url}
            target="_blank"
            rel="noopener noreferrer"
            onClick={(e) => e.stopPropagation()}
            className="px-2 py-1 text-xs hover:text-[#6366f1] transition-colors"
          >
            <ExternalLink size={12} className="inline mr-1" />
            原文
          </a>
          <button
            title={item.is_bookmarked ? "已收藏" : "收藏"}
            onClick={(e) => { e.stopPropagation(); onBookmark?.(item.id); }}
            className={`px-2 py-1 text-xs transition-colors ${
              item.is_bookmarked ? "text-[#60a5fa]" : "hover:text-[#6366f1]"
            }`}
          >
            {item.is_bookmarked ? <BookmarkCheck size={12} className="inline mr-1" /> : <Bookmark size={12} className="inline mr-1" />}
            {item.is_bookmarked ? "已收藏" : "收藏"}
          </button>
          <button
            title="屏蔽"
            onClick={(e) => { e.stopPropagation(); onHide?.(item.id); }}
            className="px-2 py-1 text-xs hover:text-[#f87171] transition-colors"
          >
            <EyeOff size={12} className="inline mr-1" />
            屏蔽
          </button>
        </div>
      </div>
    </article>
  );
}
