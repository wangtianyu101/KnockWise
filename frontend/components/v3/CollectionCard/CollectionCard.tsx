/**
 * V3 CollectionCard 组件（PR 2 · V3.1 · 5 状态 + 5 题单不同渐变色）
 */
import { PlayCircleOutlined, StarFilled } from '@ant-design/icons';

export interface QuestionCollection {
  id: string;
  name: string;
  description?: string;
  cover_color: string;
  icon_emoji: string;
  question_count: number;
  is_system: boolean;
  subscribed: boolean;
  progress?: { done_count: number; completion_rate: number; last_question_id?: string | null };
}

export function CollectionCard({
  collection,
  onStart,
  onSubscribe,
  onUnsubscribe,
  onClick,
}: {
  collection: QuestionCollection;
  onStart: (id: string) => void;
  onSubscribe: (id: string) => void;
  onUnsubscribe: (id: string) => void;
  onClick?: (id: string) => void;
}) {
  const done = collection.progress?.done_count || 0;
  const total = collection.question_count;
  const rate = total > 0 ? Math.round((done / total) * 100) : 0;
  const hasProgress = done > 0;
  const buttonLabel = !collection.subscribed
    ? '+ 订阅题单'
    : hasProgress
      ? '继续刷 →'
      : '开始 →';

  return (
    <div
      className="v3-collection-card relative cursor-pointer rounded-2xl p-6 border"
      style={{
        background: `linear-gradient(135deg, ${hexToRgba(collection.cover_color, 0.10)} 0%, ${hexToRgba(collection.cover_color, 0.06)} 100%)`,
        borderColor: `${hexToRgba(collection.cover_color, 0.25)}`,
      }}
      onClick={() => onClick?.(collection.id)}
    >
      {collection.subscribed && (
        <span className="absolute top-3 left-3 text-amber-400 text-lg">
          <StarFilled />
        </span>
      )}

      <div className="flex items-center gap-3 mb-4">
        <div
          className="w-12 h-12 rounded-xl flex items-center justify-center text-2xl"
          style={{
            background: `linear-gradient(135deg, ${collection.cover_color}, ${lighten(collection.cover_color, 20)})`,
            boxShadow: `0 4px 12px ${hexToRgba(collection.cover_color, 0.35)}`,
          }}
        >
          {collection.icon_emoji}
        </div>
        <div>
          <h3 className="text-base font-semibold text-white">{collection.name}</h3>
          {collection.description && (
            <p className="text-xs text-gray-400 line-clamp-1">{collection.description}</p>
          )}
        </div>
      </div>

      <div className="flex items-center justify-between mb-4">
        <div className="relative" style={{ width: 56, height: 56 }}>
          <svg className="ring-progress" width="56" height="56" viewBox="0 0 56 56">
            <circle className="ring-progress-bg" cx="28" cy="28" r="24" strokeWidth="4" />
            <circle
              className="ring-progress-fg"
              cx="28"
              cy="28"
              r="24"
              stroke={collection.cover_color}
              strokeWidth="4"
              strokeDasharray={150.8}
              strokeDashoffset={150.8 - (150.8 * rate) / 100}
              style={{ filter: `drop-shadow(0 0 6px ${hexToRgba(collection.cover_color, 0.5)})` }}
            />
          </svg>
          <span
            className="absolute inset-0 flex items-center justify-center text-sm font-bold"
            style={{ color: collection.cover_color, fontFeatureSettings: '"tnum"' }}
          >
            {rate}%
          </span>
        </div>
        <div className="flex-1 ml-4">
          <div className="flex justify-between text-xs">
            <span className="text-gray-400">已完成</span>
            <span
              className="font-semibold"
              style={{ color: collection.cover_color, fontFeatureSettings: '"tnum"' }}
            >
              {done} / {total}
            </span>
          </div>
          <div className="text-xs text-gray-500 mt-1">
            {collection.subscribed ? (hasProgress ? '继续坚持' : '开始刷题') : '订阅后开始'}
          </div>
        </div>
      </div>

      <button
        className="w-full h-9 rounded-lg text-sm font-medium text-white"
        style={{
          background: collection.cover_color,
          boxShadow: `0 1px 2px ${hexToRgba(collection.cover_color, 0.3)}`,
        }}
        onClick={(e) => {
          e.stopPropagation();
          if (!collection.subscribed) onSubscribe(collection.id);
          else onStart(collection.id);
        }}
        onDoubleClick={(e) => {
          e.stopPropagation();
          if (collection.subscribed) onUnsubscribe(collection.id);
        }}
        title="双击已订阅题单可取消订阅"
      >
        <PlayCircleOutlined /> {buttonLabel}
      </button>
    </div>
  );
}

// 工具：hex → rgba
function hexToRgba(hex: string, alpha: number): string {
  const h = hex.replace('#', '');
  const r = parseInt(h.substring(0, 2), 16);
  const g = parseInt(h.substring(2, 4), 16);
  const b = parseInt(h.substring(4, 6), 16);
  return `rgba(${r}, ${g}, ${b}, ${alpha})`;
}

// 工具：hex 颜色加亮
function lighten(hex: string, amount: number): string {
  const h = hex.replace('#', '');
  const r = Math.min(255, parseInt(h.substring(0, 2), 16) + amount);
  const g = Math.min(255, parseInt(h.substring(2, 4), 16) + amount);
  const b = Math.min(255, parseInt(h.substring(4, 6), 16) + amount);
  return `rgb(${r}, ${g}, ${b})`;
}
