import { useState } from 'react';

import { DigestCard } from '@/components/digest/DigestCard';
import { HideDialog } from '@/components/digest/HideDialog';
import { VibeBadge } from '@/components/digest/VibeBadge';
import { useAddBookmark, useDigestToday, useHideItem } from '@/hooks/useDigest';

export default function AiTodayPage() {
  const { data, isLoading, error } = useDigestToday();
  const addBookmark = useAddBookmark();
  const hideItem = useHideItem();
  const [bookmarkedIds, setBookmarkedIds] = useState<Set<string>>(new Set());
  const [hiddenCandidate, setHiddenCandidate] = useState<{
    id: string;
    title: string;
    topics: string[];
  } | null>(null);

  if (isLoading) {
    return <p className="text-[#94a3b8]">正在加载今日 Digest…</p>;
  }
  if (error) {
    return <p role="alert" className="text-[#fca5a5]">今日 Digest 加载失败，请稍后重试。</p>;
  }
  if (!data || data.items.length === 0) {
    return <p className="text-[#94a3b8]">今日还没有可展示的 Digest。</p>;
  }

  const bookmark = (itemId: string) => {
    setBookmarkedIds((current) => new Set(current).add(itemId));
    addBookmark.mutate(itemId);
  };

  return (
    <div>
      <header className="mb-8">
        <h1 className="text-3xl font-bold mb-3">AI 今日推荐</h1>
        <VibeBadge vibe={data.vibe} />
      </header>

      <section aria-label="今日 Digest" className="space-y-3">
        {data.items.map((item) => (
          <DigestCard
            key={item.id}
            item={{
              ...item,
              summary: item.summary ?? undefined,
              published_at: item.published_at ?? undefined,
              is_bookmarked: item.is_bookmarked || bookmarkedIds.has(item.id),
            }}
            onBookmark={bookmark}
            onHide={() => setHiddenCandidate({
              id: item.id,
              title: item.title,
              topics: [item.category, item.type],
            })}
          />
        ))}
      </section>

      {/* 底部状态栏（T3 · mockup 01-today.html L217-219） */}
      <p
        data-testid="digest-status-bar"
        className="text-center mt-8 text-[#64748b] text-[13px]"
      >
        {data.items.filter((it) => it.is_read).length}/{data.items.length} 已读 · 剩余 {Math.max(0, data.items.length - data.items.filter((it) => it.is_read).length)} 分钟 · 推送时间：每天 08:00 (Asia/Shanghai)
      </p>

      <HideDialog
        open={hiddenCandidate !== null}
        onOpenChange={(open) => !open && setHiddenCandidate(null)}
        itemTitle={hiddenCandidate?.title ?? ''}
        suggestedTopics={hiddenCandidate?.topics ?? []}
        onConfirm={(reason, keywords) => {
          if (!hiddenCandidate) return;
          hideItem.mutate({
            item_id: hiddenCandidate.id,
            reason,
            topic_keywords: keywords,
          });
        }}
      />
    </div>
  );
}
