"use client";

import { DigestCard } from "./DigestCard";
import { VibeBadge, VibeLevel } from "./VibeBadge";

export interface DigestListItem {
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

interface DigestListProps {
  items: DigestListItem[];
  vibe?: string | null;
  vibeLevel?: VibeLevel;
  readCount?: number;
  onHide?: (itemId: string) => void;
  onBookmark?: (itemId: string) => void;
  onOpenDetail?: (itemId: string) => void;
}

export function DigestList({ items, vibe, vibeLevel = "info", readCount = 0, onHide, onBookmark, onOpenDetail }: DigestListProps) {
  return (
    <div>
      <VibeBadge vibe={vibe} level={vibeLevel} />
      {items.length === 0 ? (
        <div className="text-center py-20 text-[#94a3b8]">
          <div className="text-5xl mb-3">🌙</div>
          <p>今日 AI 圈无新动态 · 周末静默</p>
        </div>
      ) : (
        <>
          {items.map((item) => (
            <DigestCard
              key={item.id}
              item={item}
              onHide={onHide}
              onBookmark={onBookmark}
              onOpenDetail={onOpenDetail}
            />
          ))}
          <p className="text-center mt-8 text-[#64748b] text-[13px]">
            {readCount}/{items.length} 已读 · 剩余 {items.length - readCount} 分钟
          </p>
        </>
      )}
    </div>
  );
}
