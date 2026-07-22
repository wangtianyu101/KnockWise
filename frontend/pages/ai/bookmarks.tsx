// pages/ai/bookmarks.tsx · T25 part of T10-T14 work
import { useState } from 'react';
import { useDigestBookmarks } from '@/hooks/useDigest';
import { VibeBadge } from '@/components/digest/VibeBadge';

export default function BookmarksPage() {
  const [filter, setFilter] = useState<'all' | 'model' | 'application'>('all');
  // 2026-07-22 audit 修复：hooks 返回 { data, isLoading, error, refetch } · 字段都在 data 里
  const { data, isLoading } = useDigestBookmarks(filter);
  const bookmarks = data?.items ?? [];
  const total = data?.total ?? 0;
  return (
    <div>
      <h1 className="text-2xl font-bold mb-4 text-text-primary">🔖 我的收藏</h1>
      <VibeBadge text={`共 ${total} 条收藏`} />
      <div className="flex gap-2 my-4">
        {(['all', 'model', 'application'] as const).map((t) => (
          <button key={t} onClick={() => setFilter(t)}
            className={`px-3 py-1 rounded text-sm ${filter === t ? 'bg-primary text-white' : 'text-text-secondary'}`}>
            {t === 'all' ? '全部' : t === 'model' ? '模型' : '应用'}
          </button>
        ))}
      </div>
      {isLoading ? <p className="text-text-secondary">加载中...</p> : (
        <div className="space-y-2">
          {bookmarks.map((b) => <div key={b.item_id} className="glass-card-static p-3">{b.title}</div>)}
        </div>
      )}
    </div>
  );
}
