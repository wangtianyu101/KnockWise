/**
 * V3.7 · AIRecommendationCard 组件（PR 6 · dashboard 顶部）
 * 4 种类型配色：[补] 红色 / [练] 蓝色 / [读] 紫色 / [盘] 琥珀
 * 失败时隐藏整张卡（决策 7A 不阻塞）
 */
import { useAIRecommendations } from '@/hooks/useAIRecommendations';

const PREFIX_COLOR: Record<string, string> = {
  '[补]': 'rgba(248,113,113,0.18)', // red
  '[练]': 'rgba(96,165,250,0.18)', // blue
  '[读]': 'rgba(167,139,250,0.18)', // violet
  '[盘]': 'rgba(245,158,11,0.18)', // amber
};

const PREFIX_TEXT: Record<string, string> = {
  '[补]': '#fca5a5',
  '[练]': '#93c5fd',
  '[读]': '#c4b5fd',
  '[盘]': '#fcd34d',
};

function RecommendationItem({ rec, onClick }: { rec: any; onClick?: () => void }) {
  const bg = PREFIX_COLOR[rec.prefix] || 'rgba(255,255,255,0.05)';
  const fg = PREFIX_TEXT[rec.prefix] || '#94a3b8';

  return (
    <button
      onClick={() => {
        // 埋点
        if (typeof window !== 'undefined') {
          console.log('[analytics] click_recommend', { topic: rec.rawTopic, priority: rec.priority });
        }
        onClick?.();
      }}
      className="recommendation-item text-left p-4 rounded-lg transition-all"
      style={{ background: bg, border: `1px solid ${fg}40` }}
    >
      <div className="flex items-center gap-2 mb-2">
        <span
          className="text-xs font-semibold px-2 py-0.5 rounded"
          style={{ color: fg, background: `${fg}20` }}
        >
          {rec.prefix}
        </span>
        <span className="text-xs text-gray-500 stat-num">
          出现 {rec.frequency} 次
        </span>
      </div>
      <p className="text-sm font-semibold text-gray-100 mb-1.5">{rec.title}</p>
      <p className="text-xs text-gray-400 line-clamp-2" style={{ lineHeight: 1.5 }}>
        {rec.description}
      </p>
      <div className="flex items-center gap-1.5 mt-3 text-xs text-indigo-400">
        <svg width="12" height="12" viewBox="0 0 12 12" fill="none">
          <path d="M2 6h8M7 3l3 3-3 3" stroke="currentColor" strokeWidth="1.4" strokeLinecap="round" strokeLinejoin="round" />
        </svg>
        <span>立即行动 →</span>
      </div>
    </button>
  );
}

export function AIRecommendationCard({ onItemClick }: { onItemClick?: (topic: string) => void }) {
  const { data, loading, error, empty } = useAIRecommendations();

  // 失败 / 加载中 / 无数据：隐藏整张卡（决策 7A）
  if (loading || error || empty || data.length === 0) return null;

  return (
    <div
      className="rounded-2xl p-8 mb-6"
      style={{
        background: 'linear-gradient(135deg, rgba(99,102,241,0.10) 0%, rgba(168,85,247,0.10) 100%)',
        border: '1px solid rgba(99,102,241,0.25)',
        boxShadow: '0 12px 40px rgba(99,102,241,0.15)',
      }}
    >
      <div className="flex items-center justify-between mb-5">
        <div className="flex items-center gap-3">
          <div
            className="w-12 h-12 rounded-2xl flex items-center justify-center"
            style={{
              background: 'linear-gradient(135deg, #6366f1, #a78bfa)',
              boxShadow: '0 8px 24px rgba(99,102,241,0.4)',
            }}
          >
            <svg width="24" height="24" viewBox="0 0 20 20" fill="none">
              <path d="M10 2L11 6L15 7L11 8L10 12L9 8L5 7L9 6L10 2Z" fill="white" />
              <path d="M16 12L16.5 13.5L18 14L16.5 14.5L16 16L15.5 14.5L14 14L15.5 13.5L16 12Z" fill="white" />
              <path d="M4 13L4.5 14L5.5 14.5L4.5 15L4 16L3.5 15L2.5 14.5L3.5 14L4 13Z" fill="white" />
            </svg>
          </div>
          <div>
            <h2 className="text-xl font-bold mb-1">今日 AI 推荐</h2>
            <p className="text-sm text-gray-400">
              基于你的面试薄弱点 · 来自 V2 recommendations_service
            </p>
          </div>
        </div>
        <span className="text-xs text-gray-500">V3.7 · {data.length} 条建议</span>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
        {data.slice(0, 4).map((rec, idx) => (
          <RecommendationItem
            key={`${rec.rawTopic}-${idx}`}
            rec={rec}
            onClick={() => onItemClick?.(rec.rawTopic)}
          />
        ))}
      </div>

      <p className="text-xs text-gray-500 mt-5 text-center">
        💡 完成更多面试后，AI 推荐会越来越精准
      </p>
    </div>
  );
}
