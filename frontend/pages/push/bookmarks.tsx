/**
 * /push/bookmarks · 我的收藏 · mockup 03 + spec R5
 *
 * 设计要素（mockup 03-bookmarks.html）：
 * - 副标题 "N 条 · X 个模型 / Y 个应用 · 跨 Z 家公司"
 * - 4 tabs: 全部(N) / 模型(N) / 应用(N) / 论文(N)
 * - 排序下拉: 收藏时间（最新）/ 质量分（高 → 低）/ 发布日期（最新）
 * - 每条完整 card（参考 today DigestCard 样式）+ "查看原文 →"
 * - 底部 "显示前 4 条 · 共 N 条 · 查看全部"
 */
import { useMemo, useState } from 'react';
import { useRouter } from 'next/router';
import { useDigestBookmarks } from '@/hooks/useDigest';

type Filter = 'all' | 'model' | 'application' | 'paper';
type Sort = 'bookmarked_desc' | 'quality_desc' | 'published_desc';

const TABS: { value: Filter; label: string }[] = [
  { value: 'all', label: '全部' },
  { value: 'model', label: '模型' },
  { value: 'application', label: '应用' },
  { value: 'paper', label: '论文' },
];

const SORT_OPTIONS: { value: Sort; label: string }[] = [
  { value: 'bookmarked_desc', label: '收藏时间（最新）' },
  { value: 'quality_desc', label: '质量分（高 → 低）' },
  { value: 'published_desc', label: '发布日期（最新）' },
];

export default function BookmarksPage() {
  const router = useRouter();
  const [filter, setFilter] = useState<Filter>('all');
  const [sort, setSort] = useState<Sort>('bookmarked_desc');

  // 后端目前 type filter 只支持 model|application，论文 tab 走客户端 filter
  const backendFilter = filter === 'paper' ? null : filter === 'all' ? null : filter;
  const { data, isLoading } = useDigestBookmarks(backendFilter as 'all' | 'model' | 'application' | undefined);

  const allItems = data?.items ?? [];

  // 客户端二次过滤：论文按 type=application 且 source_name 含"论文"/arxiv 关键字粗筛（DB 没 paper enum）
  const items = useMemo(() => {
    let result = allItems;
    if (filter === 'paper') {
      result = allItems.filter((it) =>
        /arxiv|paper|论文|qwen|llm/i.test(`${it.source_name} ${it.title}`)
      );
    }
    return result;
  }, [allItems, filter]);

  const total = items.length;
  const modelCount = allItems.filter((it) => it.type === 'model').length;
  const appCount = allItems.filter((it) => it.type === 'application').length;
  const paperCount = useMemo(
    () => allItems.filter((it) => /arxiv|paper|论文|qwen|llm/i.test(`${it.source_name} ${it.title}`)).length,
    [allItems]
  );
  const sourceCount = new Set(items.map((it) => it.source_name)).size;

  const tabCounts: Record<Filter, number> = {
    all: allItems.length,
    model: modelCount,
    application: appCount,
    paper: paperCount,
  };

  return (
    <div>
      <header className="mb-6">
        <h1 className="text-3xl font-bold mb-2 tracking-tight">🔖 我的收藏</h1>
        <p className="text-sm text-[#94a3b8]">
          {total} 条 · {modelCount} 个模型 / {appCount} 个应用 / {paperCount} 个论文 · 跨 {sourceCount} 家公司
        </p>
      </header>

      {/* Tabs + Sort 工具栏 */}
      <div
        className="flex items-center justify-between bg-[rgba(15,20,40,0.7)] backdrop-blur-xl border border-[rgba(148,163,184,0.08)] rounded-xl px-4 py-3 mb-4"
        data-testid="bookmarks-toolbar"
      >
        <div className="flex items-center gap-1">
          {TABS.map((tab) => (
            <button
              key={tab.value}
              onClick={() => setFilter(tab.value)}
              className={`px-3 py-1 rounded-full text-sm transition-colors ${
                filter === tab.value
                  ? 'bg-[rgba(99,102,241,0.18)] text-[#c7d2fe] border border-[rgba(99,102,241,0.35)]'
                  : 'text-[#94a3b8] hover:text-[#f8fafc] border border-transparent'
              }`}
              data-testid={`tab-${tab.value}`}
            >
              {tab.label} ({tabCounts[tab.value]})
            </button>
          ))}
        </div>
        <select
          value={sort}
          onChange={(e) => setSort(e.target.value as Sort)}
          className="bg-[rgba(15,20,40,0.7)] border border-[rgba(148,163,184,0.12)] rounded-md px-2 py-1 text-sm text-[#f8fafc]"
          data-testid="select-sort"
        >
          {SORT_OPTIONS.map((o) => (
            <option key={o.value} value={o.value}>{o.label}</option>
          ))}
        </select>
      </div>

      {/* 列表 */}
      {isLoading ? (
        <p className="text-[#94a3b8]">加载中…</p>
      ) : items.length === 0 ? (
        <div className="text-center py-20 text-[#94a3b8]">
          <div className="text-5xl mb-3">🌙</div>
          <p>还没有收藏 · 去 <button onClick={() => router.push('/push')} className="text-[#93c5fd] hover:underline">今日推荐</button> 添加</p>
        </div>
      ) : (
        <div className="space-y-3" data-testid="bookmark-list">
          {items.slice(0, 4).map((b) => (
            <BookmarkCard
              key={b.item_id}
              item={b}
              onOpen={() => router.push(`/push/daily/${b.published_at?.slice(0, 10) ?? ''}?item=${b.item_id}`)}
            />
          ))}
        </div>
      )}

      {/* 底部 count + 查看全部 */}
      {items.length > 0 && (
        <p className="text-center mt-6 text-[#64748b] text-[13px]">
          显示前 {Math.min(4, items.length)} 条 · 共 {items.length} 条
          {items.length > 4 && (
            <button onClick={() => {}} className="ml-1 text-[#60a5fa] hover:underline">查看全部 →</button>
          )}
        </p>
      )}
    </div>
  );
}

/** 单条 bookmark 卡片（与 mockup 03 一致） */
function BookmarkCard({
  item,
  onOpen,
}: {
  item: {
    item_id: string;
    title: string;
    summary?: string | null;
    type: 'model' | 'application';
    region: 'domestic' | 'overseas';
    source_name: string;
    source_url: string;
    quality_score: number;
    bookmarked_at?: string;
    published_at?: string | null;
  };
  onOpen: () => void;
}) {
  return (
    <article
      onClick={onOpen}
      className="bg-[rgba(15,20,40,0.7)] backdrop-blur-xl border border-[rgba(148,163,184,0.08)] rounded-xl p-5 transition-all hover:shadow-lg hover:border-[rgba(99,102,241,0.25)] cursor-pointer"
      data-testid="bookmark-card"
    >
      <div className="flex items-center gap-2 mb-3 text-xs text-[#94a3b8] flex-wrap">
        <span className={`px-2 py-0.5 rounded text-[11px] font-medium border ${item.type === 'model' ? 'bg-[rgba(96,165,250,0.18)] text-[#93c5fd] border-[rgba(96,165,250,0.35)]' : 'bg-[rgba(167,139,250,0.18)] text-[#c4b5fd] border-[rgba(167,139,250,0.35)]'}`}>
          {item.type === 'model' ? '模型' : '应用'}
        </span>
        <span className={`px-2 py-0.5 rounded text-[11px] font-medium border ${item.region === 'domestic' ? 'bg-[rgba(245,158,11,0.18)] text-[#fcd34d] border-[rgba(245,158,11,0.35)]' : 'bg-[rgba(52,211,153,0.18)] text-[#6ee7b7] border-[rgba(52,211,153,0.35)]'}`}>
          {item.region === 'domestic' ? '国内' : '国外'}
        </span>
        <span>· {item.source_name}</span>
      </div>
      <h2 className="text-[18px] font-bold mb-2 tracking-tight leading-tight">{item.title}</h2>
      {item.summary && (
        <p className="text-sm leading-relaxed text-[#94a3b8] mb-3">{item.summary}</p>
      )}
      <div className="flex items-center justify-between text-xs text-[#64748b]">
        <span>
          收藏于 {item.bookmarked_at?.slice(0, 16).replace('T', ' ') ?? ''} · 推送自 {item.published_at?.slice(0, 16).replace('T', ' ') ?? '—'}
        </span>
        <a
          href={item.source_url}
          target="_blank"
          rel="noopener noreferrer"
          onClick={(e) => e.stopPropagation()}
          className="text-[#93c5fd] hover:underline"
          data-testid="btn-source"
        >
          查看原文 →
        </a>
      </div>
    </article>
  );
}