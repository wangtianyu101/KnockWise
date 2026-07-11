/**
 * HeroCard 组件 — V3.8 P2 核心
 *
 * Dashboard 顶部 60% 视觉权重 · 5 状态机
 * spec §3.1 · design-spec §3.1.3
 *
 * 5 状态：
 * - full（3 雷达 + 上次成绩 + 主按钮）
 * - partial（1-2 雷达 + 虚线占位）
 * - empty（EmptyState + "开始第一次面试"）
 * - loading（skeleton + 不可点击）
 * - error（红色警告 + 重试）
 *
 * ⚠️ Tailwind 4 在 Next.js dev 模式 CSS 不输出（v3 遗留 bug）·
 *    关键视觉用 inline style 兜底
 */
import React from 'react';
import type { InterviewRecentItem } from '@/types/interview';

export type HeroState = 'full' | 'partial' | 'empty' | 'loading' | 'error';

export interface HeroCardProps {
  /** 上次面试数据（最高分的那条）*/
  lastInterview?: InterviewRecentItem;
  /** 最近 N 次面试（用于迷你雷达）*/
  recentInterviews: InterviewRecentItem[];
  /** 总面试数（近 30 天）*/
  totalInterviews: number;
  /** 平均分（近 30 天）*/
  avgScore: number | null;
  /** 当前状态（覆盖自动判定）*/
  state?: HeroState;
  /** 加载状态 */
  loading?: boolean;
  /** 点击"开始面试"回调 */
  onStartInterview?: () => void;
  /** 点击"查看历史"回调 */
  onViewHistory?: () => void;
  /** 点击"配置面试偏好"回调 */
  onConfigInterview?: () => void;
  /** 点击"重试"回调（error 状态）*/
  onRetry?: () => void;
  /** 测试用 */
  "data-testid"?: string;
}

// HeroCard 渐变色（粉紫 · mockup L981）
const HERO_GRADIENT = 'linear-gradient(135deg, rgba(244,114,182,0.15) 0%, rgba(236,72,153,0.12) 50%, rgba(168,85,247,0.15) 100%)';
const HERO_BORDER = 'rgba(244,114,182,0.4)';
const HERO_SHADOW = '0 16px 48px rgba(244,114,182,0.3)';

// 自动状态判定
function determineState(props: HeroCardProps): HeroState {
  if (props.state) return props.state;
  if (props.loading) return 'loading';
  if (props.recentInterviews.length === 0) return 'empty';
  if (props.recentInterviews.length < 3) return 'partial';
  return 'full';
}

// 单个 RadarMini SVG
function MiniRadar({
  data,
  color,
  size = 80,
  placeholder = false,
}: {
  data?: InterviewRecentItem['radar_data'];
  color: string;
  size?: number;
  placeholder?: boolean;
}) {
  if (placeholder) {
    return (
      <svg viewBox="0 0 80 80" width={size} height={size} aria-hidden="true">
        <polygon
          points="40,8 70,28 60,68 20,68 10,28"
          fill="none"
          stroke="rgba(255,255,255,0.1)"
          strokeWidth="1"
          strokeDasharray="3 3"
        />
      </svg>
    );
  }
  if (!data) return null;
  // 计算 5 边形数据点（algorithm → ai 顺序）
  const dims = ['algorithm', 'system_design', 'network', 'frontend', 'ai'] as const;
  const cx = 40, cy = 40;
  // 5 边形顶点（顺时针）
  const vertices = [
    { x: cx, y: 8 },
    { x: 70, y: 28 },
    { x: 60, y: 68 },
    { x: 20, y: 68 },
    { x: 10, y: 28 },
  ];
  const points = vertices.map((v, i) => {
    const dim = dims[i];
    const value = data[dim] ?? 0;
    const ratio = Math.min(1, Math.max(0, value / 100));
    return {
      x: cx + (v.x - cx) * ratio,
      y: cy + (v.y - cy) * ratio,
    };
  });
  const polygonPoints = points.map(p => `${p.x},${p.y}`).join(' ');

  return (
    <svg viewBox="0 0 80 80" width={size} height={size} aria-hidden="true">
      <polygon
        points="40,8 70,28 60,68 20,68 10,28"
        fill="none"
        stroke={`${color}26`}  // 15% opacity
        strokeWidth="1"
      />
      <polygon
        points={polygonPoints}
        fill={`${color}40`}  // 25% opacity
        stroke={color}
        strokeWidth="1.5"
      />
    </svg>
  );
}

export function HeroCard({
  lastInterview,
  recentInterviews,
  totalInterviews,
  avgScore,
  state: stateProp,
  loading,
  onStartInterview,
  onViewHistory,
  onConfigInterview,
  onRetry,
  'data-testid': testId = 'hero-card',
}: HeroCardProps) {
  const state = determineState({ state: stateProp, loading, recentInterviews });

  // ── Full 状态 ─────────────────────────────────────────
  if (state === 'full') {
    const radarColors = ['#f472b6', '#a78bfa', '#60a5fa']; // 粉/紫/蓝
    const companies = ['字节', '阿里', '腾讯'];
    const displayRadars = [...recentInterviews];
    while (displayRadars.length < 3) displayRadars.push(recentInterviews[recentInterviews.length - 1]);

    return (
      <div
        data-testid={testId}
        className="hero-card"
        style={{
          background: HERO_GRADIENT,
          border: `1px solid ${HERO_BORDER}`,
          boxShadow: HERO_SHADOW,
          borderRadius: 16,
          padding: 48,
          marginBottom: 40,
          color: '#f8fafc',
          display: 'grid',
          gridTemplateColumns: '3fr 2fr',
          gap: 32,
          alignItems: 'center',
        }}
      >
        {/* 左 3 列：主任务 + 上次成绩 + 主按钮 */}
        <div>
          <div style={{ display: 'flex', alignItems: 'center', gap: 12, marginBottom: 20 }}>
            <span style={{
              background: 'rgba(244,114,182,0.2)',
              color: '#fbcfe8',
              border: '1px solid rgba(244,114,182,0.4)',
              padding: '6px 14px',
              borderRadius: 6,
              fontSize: 13,
              fontWeight: 600,
            }}>🎤 今日主任务</span>
            <span style={{
              background: 'rgba(148,163,184,0.06)',
              color: '#94a3b8',
              padding: '6px 14px',
              borderRadius: 6,
              fontSize: 13,
            }}>未完成</span>
          </div>
          <h2 style={{
            fontSize: 30,
            fontWeight: 700,
            lineHeight: 1.1,
            margin: '0 0 20px',
            background: 'linear-gradient(90deg, #f472b6, #a78bfa, #6366f1)',
            WebkitBackgroundClip: 'text',
            WebkitTextFillColor: 'transparent',
            backgroundClip: 'text',
          }}>
            开始一场 <span>Mock 面试</span>
          </h2>
          <p style={{
            color: '#cbd5e1',
            fontSize: 16,
            lineHeight: 1.7,
            margin: '0 0 32px',
            maxWidth: 560,
          }}>
            系统会根据你的薄弱点（缓存一致性 · 分布式系统）智能选题 · 30 分钟掌握一轮 · 自动生成雷达报告与知识沉淀。
          </p>

          {/* 上次成绩 3 栏 */}
          <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr 1fr', gap: 16, marginBottom: 32 }}>
            <div>
              <p style={{ fontSize: 12, color: '#64748b', textTransform: 'uppercase', letterSpacing: '0.08em', margin: '0 0 6px' }}>上次面试</p>
              <p style={{ fontSize: 24, fontWeight: 700, color: '#f472b6', margin: 0, fontVariantNumeric: 'tabular-nums' }}>
                {lastInterview?.overall_score ?? '-'}
                <span style={{ fontSize: 14, color: '#64748b' }}>/100</span>
              </p>
              <p style={{ fontSize: 12, color: '#64748b', margin: '4px 0 0' }}>{lastInterview?.round ?? '-'}</p>
            </div>
            <div>
              <p style={{ fontSize: 12, color: '#64748b', textTransform: 'uppercase', letterSpacing: '0.08em', margin: '0 0 6px' }}>已面试</p>
              <p style={{ fontSize: 24, fontWeight: 700, color: '#f8fafc', margin: 0, fontVariantNumeric: 'tabular-nums' }}>
                {totalInterviews}<span style={{ fontSize: 14, color: '#64748b' }}>次</span>
              </p>
              <p style={{ fontSize: 12, color: '#64748b', margin: '4px 0 0' }}>近 30 天</p>
            </div>
            <div>
              <p style={{ fontSize: 12, color: '#64748b', textTransform: 'uppercase', letterSpacing: '0.08em', margin: '0 0 6px' }}>平均分</p>
              <p style={{ fontSize: 24, fontWeight: 700, color: '#34d399', margin: 0, fontVariantNumeric: 'tabular-nums' }}>
                {avgScore ?? '-'}
                <span style={{ fontSize: 14, color: '#64748b' }}>/100</span>
              </p>
              <p style={{ fontSize: 12, color: '#34d399', margin: '4px 0 0' }}>+6 ↑</p>
            </div>
          </div>

          {/* 主操作按钮 */}
          <div style={{ display: 'flex', alignItems: 'center', gap: 12 }}>
            <button
              onClick={onStartInterview}
              style={{
                background: '#6366f1',
                color: 'white',
                padding: '14px 32px',
                fontSize: 16,
                fontWeight: 600,
                border: 'none',
                borderRadius: 10,
                cursor: 'pointer',
                boxShadow: '0 8px 24px rgba(99,102,241,0.4)',
              }}
            >开始面试 →</button>
            <button
              onClick={onViewHistory}
              style={{
                background: 'rgba(255,255,255,0.04)',
                color: '#f8fafc',
                padding: '14px 22px',
                fontSize: 15,
                border: '1px solid rgba(148,163,184,0.08)',
                borderRadius: 10,
                cursor: 'pointer',
              }}
            >查看历史</button>
            <button
              onClick={onConfigInterview}
              style={{
                background: 'transparent',
                color: '#94a3b8',
                padding: '14px 12px',
                fontSize: 14,
                border: 'none',
                cursor: 'pointer',
              }}
            >配置面试偏好 ⚙</button>
          </div>
        </div>

        {/* 右 2 列：3 个迷你雷达 */}
        <div>
          <p style={{
            fontSize: 12,
            color: '#64748b',
            textTransform: 'uppercase',
            letterSpacing: '0.08em',
            margin: '0 0 12px',
            textAlign: 'center',
          }}>最近 3 次雷达</p>
          <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr 1fr', gap: 8 }}>
            {displayRadars.slice(0, 3).map((iv, i) => (
              <div key={iv.id ?? i} style={{ textAlign: 'center' }}>
                <MiniRadar data={iv.radar_data} color={radarColors[i]} />
                <p style={{ fontSize: 12, color: '#94a3b8', margin: '4px 0 0', fontVariantNumeric: 'tabular-nums' }}>
                  {iv.overall_score ?? '-'}
                </p>
                <p style={{ fontSize: 12, color: '#64748b', margin: 0 }}>{companies[i]}</p>
              </div>
            ))}
          </div>
          <button
            onClick={onViewHistory}
            style={{
              background: 'transparent',
              color: '#94a3b8',
              padding: '8px 12px',
              fontSize: 12,
              border: 'none',
              cursor: 'pointer',
              width: '100%',
              marginTop: 12,
            }}
          >查看全部 {totalInterviews} 场面试 →</button>
        </div>
      </div>
    );
  }

  // ── Partial 状态 ─────────────────────────────────────
  if (state === 'partial') {
    const needed = 3 - recentInterviews.length;
    const displayRadars = [...recentInterviews];
    while (displayRadars.length < 3) displayRadars.push(null); // null = placeholder

    return (
      <div
        data-testid={testId}
        className="hero-card"
        style={{
          background: HERO_GRADIENT,
          border: `1px solid ${HERO_BORDER}`,
          boxShadow: HERO_SHADOW,
          borderRadius: 16,
          padding: 48,
          marginBottom: 40,
          color: '#f8fafc',
          textAlign: 'center',
        }}
      >
        <h2 style={{ fontSize: 24, fontWeight: 700, margin: '0 0 12px' }}>
          📊 已完成 {recentInterviews.length} 次面试
        </h2>
        <p style={{ color: '#94a3b8', fontSize: 16, margin: '0 0 24px' }}>
          再完成 {needed} 次即可查看完整 3 雷达
        </p>
        <div style={{ display: 'flex', justifyContent: 'center', gap: 24, marginBottom: 24 }}>
          {displayRadars.map((iv, i) => (
            <div key={i} style={{ textAlign: 'center' }}>
              <MiniRadar data={iv?.radar_data} color="#f472b6" placeholder={!iv} />
              <p style={{ fontSize: 14, color: '#94a3b8', margin: '8px 0 0' }}>{iv?.overall_score ?? '-'}</p>
              <p style={{ fontSize: 12, color: '#64748b', margin: 0 }}>{iv?.round?.split('·')[0] ?? '?'}</p>
            </div>
          ))}
        </div>
        <button
          onClick={onStartInterview}
          style={{
            background: '#6366f1',
            color: 'white',
            padding: '14px 32px',
            fontSize: 16,
            fontWeight: 600,
            border: 'none',
            borderRadius: 10,
            cursor: 'pointer',
          }}
        >开始第 {recentInterviews.length + 1} 次 →</button>
      </div>
    );
  }

  // ── Empty 状态 ───────────────────────────────────────
  if (state === 'empty') {
    return (
      <div
        data-testid={testId}
        className="hero-card"
        style={{
          background: HERO_GRADIENT,
          border: `1px solid ${HERO_BORDER}`,
          boxShadow: HERO_SHADOW,
          borderRadius: 16,
          padding: 48,
          marginBottom: 40,
          color: '#f8fafc',
          textAlign: 'center',
        }}
      >
        <svg width="80" height="80" viewBox="0 0 56 56" fill="none" style={{ margin: '0 auto 16px' }}>
          <circle cx="28" cy="28" r="20" stroke="#a78bfa" strokeWidth="1.5" strokeDasharray="4 4" opacity="0.6" />
          <path d="M28 16v12M28 36v2" stroke="#a78bfa" strokeWidth="2" strokeLinecap="round" opacity="0.6" />
        </svg>
        <h2 style={{ fontSize: 24, fontWeight: 700, margin: '0 0 12px' }}>
          还没有面试记录
        </h2>
        <p style={{ color: '#94a3b8', fontSize: 16, margin: '0 auto 24px', maxWidth: 480 }}>
          完成第 1 次面试后，Hero 卡将展示你的最近 3 次雷达 + 上次成绩
        </p>
        <button
          onClick={onStartInterview}
          style={{
            background: '#6366f1',
            color: 'white',
            padding: '14px 32px',
            fontSize: 16,
            fontWeight: 600,
            border: 'none',
            borderRadius: 10,
            cursor: 'pointer',
          }}
        >开始第一次面试 →</button>
      </div>
    );
  }

  // ── Loading 状态 ─────────────────────────────────────
  if (state === 'loading') {
    return (
      <div
        data-testid={testId}
        className="hero-card"
        style={{
          background: HERO_GRADIENT,
          border: `1px solid ${HERO_BORDER}`,
          boxShadow: HERO_SHADOW,
          borderRadius: 16,
          padding: 48,
          marginBottom: 40,
          color: '#f8fafc',
          opacity: 0.7,
        }}
      >
        <div style={{ display: 'grid', gridTemplateColumns: '3fr 2fr', gap: 32, alignItems: 'center' }}>
          <div data-testid="hero-skeleton">
            <div className="skeleton" style={{ height: 28, width: 100, marginBottom: 12 }} />
            <div className="skeleton" style={{ height: 40, width: '80%', marginBottom: 16 }} />
            <div className="skeleton" style={{ height: 16, width: '100%', marginBottom: 8 }} />
            <div className="skeleton" style={{ height: 16, width: '90%', marginBottom: 32 }} />
            <div className="skeleton" style={{ height: 48, width: 160 }} />
          </div>
          <div data-testid="hero-skeleton-radar">
            <div className="skeleton" style={{ height: 12, width: '60%', margin: '0 auto 12px' }} />
            <div className="skeleton" style={{ height: 80 }} />
          </div>
        </div>
      </div>
    );
  }

  // ── Error 状态 ────────────────────────────────────────
  return (
    <div
      data-testid={testId}
      className="hero-card"
      style={{
        background: HERO_GRADIENT,
        border: `1px solid ${HERO_BORDER}`,
        boxShadow: HERO_SHADOW,
        borderRadius: 16,
        padding: 48,
        marginBottom: 40,
        color: '#f8fafc',
        textAlign: 'center',
      }}
    >
      <svg width="80" height="80" viewBox="0 0 56 56" fill="none" style={{ margin: '0 auto 16px' }}>
        <path d="M28 8L48 44L8 44L28 8Z" stroke="#f87171" strokeWidth="2" strokeLinejoin="round" />
        <path d="M28 22v10M28 38v2" stroke="#f87171" strokeWidth="2.5" strokeLinecap="round" />
      </svg>
      <h2 style={{ fontSize: 24, fontWeight: 700, margin: '0 0 12px', color: '#fca5a5' }}>
        加载失败
      </h2>
      <p style={{ color: '#94a3b8', fontSize: 16, margin: '0 0 8px' }}>
        服务暂时不可用，请稍后重试
      </p>
      <p style={{ color: '#64748b', fontSize: 12, margin: '0 0 24px' }}>
        错误码：INTERNAL_ERROR
      </p>
      <button
        onClick={onRetry}
        style={{
          background: 'rgba(248,113,113,0.1)',
          color: '#f87171',
          padding: '14px 32px',
          fontSize: 16,
          fontWeight: 600,
          border: '1px solid rgba(248,113,113,0.2)',
          borderRadius: 10,
          cursor: 'pointer',
        }}
      >重试</button>
    </div>
  );
}

export default HeroCard;