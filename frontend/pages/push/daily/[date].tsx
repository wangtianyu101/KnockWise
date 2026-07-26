/**
 * /push/daily/[date] · 单条 digest 详情页 · v2 mockup 02 + spec R7/R10 30s 阅读时长
 *
 * 路由：
 *   /push/daily/2026-07-17         → 当日 top item
 *   /push/daily/2026-07-17?item=X  → 指定 item
 *
 * 数据：useDigestDate(date) → GET /api/digest/daily/{date}
 * 404：当日无 digest → EmptyState + 返回今日
 *
 * spec R7 + R10: 详情页 mount 后 30s → POST /api/digest/read
 */
import { useEffect, useRef, useState } from "react";
import { useRouter } from "next/router";
import Link from "next/link";

import { HideDialog } from "@/components/digest/HideDialog";
import {
  useAddBookmark,
  useDigestDate,
  useHideItem,
  useMarkRead,
  useRemoveBookmark,
} from "@/hooks/useDigest";

const READ_THRESHOLD_SEC = 30;  // spec R7/R10: 30s+ 标已读

const TYPE_COLORS: Record<"model" | "application", string> = {
  model: "bg-[rgba(96,165,250,0.18)] text-[#93c5fd] border-[rgba(96,165,250,0.35)]",
  application: "bg-[rgba(167,139,250,0.18)] text-[#c4b5fd] border-[rgba(167,139,250,0.35)]",
};

const REGION_COLORS: Record<"domestic" | "overseas", string> = {
  domestic: "bg-[rgba(245,158,11,0.18)] text-[#fcd34d] border-[rgba(245,158,11,0.35)]",
  overseas: "bg-[rgba(52,211,153,0.18)] text-[#6ee7b7] border-[rgba(52,211,153,0.35)]",
};

function formatRelative(publishedAt: string | null): string {
  if (!publishedAt) return "";
  const ts = new Date(publishedAt).getTime();
  if (Number.isNaN(ts)) return publishedAt;
  const diffSec = Math.max(0, Math.floor((Date.now() - ts) / 1000));
  if (diffSec < 3600) return `${Math.max(1, Math.floor(diffSec / 60))} 分钟前`;
  if (diffSec < 86400) return `${Math.floor(diffSec / 3600)} 小时前`;
  return `${Math.floor(diffSec / 86400)} 天前`;
}

function formatFull(publishedAt: string | null): string {
  if (!publishedAt) return "";
  const d = new Date(publishedAt);
  if (Number.isNaN(d.getTime())) return publishedAt;
  return d.toLocaleString("zh-CN", { hour12: false });
}

export default function DailyDetailPage() {
  const router = useRouter();
  const date = typeof router.query.date === "string" ? router.query.date : undefined;
  const itemQuery = typeof router.query.item === "string" ? router.query.item : undefined;

  const { data, isLoading, error, refetch } = useDigestDate(date);
  const addBookmark = useAddBookmark();
  const removeBookmark = useRemoveBookmark();
  const hideItem = useHideItem();
  const markRead = useMarkRead();

  // Hooks 必须无条件在 early return 之前调用（Rules of Hooks）
  const items = data?.items ?? [];
  const item = (itemQuery && items.find((it) => it.id === itemQuery)) || items[0];
  const [hideCandidate, setHideCandidate] = useState<{
    id: string;
    title: string;
    topics: string[];
  } | null>(null);
  const readStartRef = useRef<number>(Date.now());
  const markReadFiredRef = useRef<boolean>(false);
  useEffect(() => {
    readStartRef.current = Date.now();
    markReadFiredRef.current = false;
  }, [item?.id]);
  useEffect(() => {
    if (!item || markReadFiredRef.current) return;
    const timer = setTimeout(() => {
      const duration = Math.round((Date.now() - readStartRef.current) / 1000);
      if (duration < READ_THRESHOLD_SEC) return;
      markReadFiredRef.current = true;
      markRead.mutate({ item_id: item.id, duration_sec: duration });
    }, READ_THRESHOLD_SEC * 1000);
    return () => clearTimeout(timer);
  }, [item?.id, markRead]);

  // 404
  if (error) {
    const isNotFound = (error as Error & { status?: number }).status === 404 || /404|NO_DAILY/i.test(error.message);
    if (isNotFound) {
      return (
        <div>
          <Link href="/push" className="inline-block mb-6 px-3 py-1 rounded text-sm text-[#94a3b8] hover:bg-[rgba(255,255,255,0.04)]">
            ← 返回今日 5 条
          </Link>
          <div
            className="text-center py-20 text-[#94a3b8]"
            data-testid="empty-state"
          >
            <div className="text-5xl mb-3">🌙</div>
            <p className="text-base mb-2 text-[#f8fafc]">{date ?? "该日"} 暂无 digest</p>
            <p className="text-sm mb-6">推送历史可在每天 08:00 (Asia/Shanghai) 后查看</p>
            <Link href="/push" className="inline-block px-5 py-2 rounded-lg bg-[#6366f1] text-white text-sm font-medium hover:bg-[#4f46e5]">
              返回今日
            </Link>
          </div>
        </div>
      );
    }
    // 其他错误
    return (
      <div>
        <div className="mb-4 p-4 rounded-lg bg-[rgba(248,113,113,0.1)] border border-[rgba(248,113,113,0.3)] text-[#fca5a5]">
          加载失败 · {error.message}
          <button onClick={() => refetch()} className="ml-3 px-3 py-1 rounded text-sm border border-[rgba(248,113,113,0.4)] hover:bg-[rgba(248,113,113,0.15)]">
            重试
          </button>
        </div>
      </div>
    );
  }

  if (isLoading || !data) {
    return (
      <div data-testid="loading-skeleton">
        <div className="h-4 w-24 bg-[rgba(148,163,184,0.1)] rounded mb-6" />
        <div className="h-8 w-3/4 bg-[rgba(148,163,184,0.1)] rounded mb-4" />
        <div className="h-4 w-full bg-[rgba(148,163,184,0.1)] rounded mb-2" />
        <div className="h-4 w-5/6 bg-[rgba(148,163,184,0.1)] rounded" />
      </div>
    );
  }

  if (!item) {
    return (
      <div>
        <Link href="/push" className="inline-block mb-6 px-3 py-1 rounded text-sm text-[#94a3b8] hover:bg-[rgba(255,255,255,0.04)]">
          ← 返回今日 5 条
        </Link>
        <div className="text-center py-20 text-[#94a3b8]">
          <p>该 digest 不存在或已被删除</p>
        </div>
      </div>
    );
  }

  const toggleBookmark = () => {
    if (item.is_bookmarked) {
      removeBookmark.mutate(item.id);
    } else {
      addBookmark.mutate(item.id);
    }
  };

  const onShare = async () => {
    try {
      if (typeof navigator !== "undefined" && navigator.share) {
        await navigator.share({ title: item.title, url: item.source_url });
      } else if (typeof navigator !== "undefined" && navigator.clipboard) {
        await navigator.clipboard.writeText(item.source_url);
      }
    } catch {
      // 用户取消分享
    }
  };

  return (
    <div data-testid="daily-detail">
      <Link
        href="/push"
        className="inline-block mb-6 px-3 py-1 rounded text-sm text-[#94a3b8] hover:bg-[rgba(255,255,255,0.04)] hover:text-[#f8fafc]"
      >
        ← 返回今日 5 条
      </Link>

      <article
        className="bg-[rgba(15,20,40,0.7)] backdrop-blur-xl border border-[rgba(148,163,184,0.08)] rounded-xl p-6"
        data-testid="daily-article"
      >
        {/* 标签 + 元信息行 */}
        <div className="flex items-center gap-2 mb-5 text-[13px] text-[#94a3b8] flex-wrap">
          <span className={`px-2 py-0.5 rounded text-[11px] font-medium border ${TYPE_COLORS[item.type]}`}>
            {item.type === "model" ? "模型" : "应用"}
          </span>
          <span className={`px-2 py-0.5 rounded text-[11px] font-medium border ${REGION_COLORS[item.region]}`}>
            {item.region === "domestic" ? "国内" : "国外"}
          </span>
          <span>· {item.source_name}</span>
          {item.published_at && (
            <span suppressHydrationWarning>· {formatRelative(item.published_at)}</span>
          )}
          <span>· <span className="text-[#f59e0b]">⭐ {item.quality_score}</span></span>
          <span>· ⏱ {item.estimated_minutes} 分钟</span>
        </div>

        {/* 标题 */}
        <h1
          className="text-[28px] md:text-[32px] font-bold tracking-tight leading-tight mb-6"
          data-testid="daily-title"
        >
          {item.title}
        </h1>

        {/* 摘要 */}
        {item.summary && (
          <p className="text-base leading-relaxed text-[#cbd5e1] mb-6" data-testid="daily-summary">
            {item.summary}
          </p>
        )}

        {/* 原文来源块 */}
        <div
          className="bg-[rgba(99,102,241,0.05)] border border-[rgba(99,102,241,0.2)] rounded-lg p-4 mb-6"
          data-testid="source-block"
        >
          <p className="text-[11px] uppercase tracking-wider text-[#64748b] mb-2">📰 原文来源</p>
          <p className="font-semibold mb-2 text-[#f8fafc]">{item.source_name}</p>
          <a
            href={item.source_url}
            target="_blank"
            rel="noopener noreferrer"
            className="text-[#93c5fd] text-sm break-all hover:underline"
          >
            {item.source_url}
          </a>
          {item.published_at && (
            <p className="text-xs text-[#64748b] mt-2">发布于 {formatFull(item.published_at)}</p>
          )}
        </div>

        {/* 操作按钮 */}
        <div
          className="flex items-center gap-3 py-4 border-t border-b border-[rgba(148,163,184,0.08)]"
          data-testid="actions"
        >
          <button
            onClick={toggleBookmark}
            disabled={addBookmark.isPending || removeBookmark.isPending}
            className={`px-4 py-2 rounded-md text-sm font-medium border transition-colors ${
              item.is_bookmarked
                ? "text-[#60a5fa] border-[rgba(96,165,250,0.4)] bg-[rgba(96,165,250,0.08)]"
                : "text-[#94a3b8] border-[rgba(148,163,184,0.2)] hover:border-[rgba(99,102,241,0.4)]"
            }`}
            data-testid="btn-bookmark"
          >
            {item.is_bookmarked ? "✓ 已收藏" : "🔖 收藏"}
          </button>
          <button
            onClick={onShare}
            className="px-4 py-2 rounded-md text-sm font-medium border border-[rgba(148,163,184,0.2)] text-[#94a3b8] hover:border-[rgba(99,102,241,0.4)]"
            data-testid="btn-share"
          >
            📤 分享
          </button>
          <button
            onClick={() => setHideCandidate({
              id: item.id,
              title: item.title,
              topics: [item.category, item.type, item.region],
            })}
            className="px-4 py-2 rounded-md text-sm font-medium border border-[rgba(248,113,113,0.3)] text-[#fca5a5] hover:bg-[rgba(248,113,113,0.1)]"
            data-testid="btn-hide"
          >
            🔇 不再推送类似
          </button>
        </div>
      </article>

      {/* 相关历史 digest */}
      <section className="mt-10" data-testid="related-section">
        <p className="text-sm font-semibold text-[#64748b] mb-4 uppercase tracking-wider">
          📚 相关历史 digest
        </p>
        {item.related_item_ids && item.related_item_ids.length > 0 ? (
          <div className="space-y-2" data-testid="related-list">
            <p className="text-sm text-[#94a3b8]">
              该条与历史 {item.related_item_ids.length} 条 digest 相关 · 详情见历史浏览
            </p>
            <Link
              href={`/ai/history`}
              className="inline-block mt-2 text-sm text-[#93c5fd] hover:underline"
            >
              查看完整历史 →
            </Link>
          </div>
        ) : (
          <p className="text-sm text-[#64748b]" data-testid="related-empty">
            暂无相关历史
          </p>
        )}
      </section>

      {/* HideDialog 复用 */}
      <HideDialog
        open={hideCandidate !== null}
        onOpenChange={(open) => !open && setHideCandidate(null)}
        itemTitle={hideCandidate?.title ?? ""}
        suggestedTopics={hideCandidate?.topics ?? []}
        onConfirm={(reason, keywords) => {
          if (!hideCandidate) return;
          hideItem.mutate({
            item_id: hideCandidate.id,
            reason,
            topic_keywords: keywords,
          });
        }}
      />
    </div>
  );
}