/**
 * StatsBar 组件 — V3.8 P2
 *
 * 5 列横条统计（spec §3.2 · design-spec §3.2）
 * - 本周答题 / 命中率 / 待复习 / 连续打卡 / 已完成
 *
 * ⚠️ 关键视觉用 inline style 兜底（Tailwind 4 dev mode 不输出）
 */
import React from 'react';

export interface StatsBarStat {
  label: string;
  value: string | number;
  unit?: string;
  trend?: 'up' | 'down' | 'neutral';
  trendValue?: string;
  trendColor?: 'emerald' | 'amber' | 'red' | 'gray';
  trendArrow?: '↑' | '↓' | '→';
}

export interface StatsBarProps {
  stats: StatsBarStat[];
  loading?: boolean;
  "data-testid"?: string;
}

const TREND_COLOR_MAP: Record<NonNullable<StatsBarStat['trendColor']>, string> = {
  emerald: '#34d399',
  amber: '#fbbf24',
  red: '#f87171',
  gray: '#94a3b8',
};

function Skeleton() {
  return <div className="skeleton" style={{ height: 40, borderRadius: 6 }} />;
}

export function StatsBar({ stats, loading, 'data-testid': testId = 'stats-bar' }: StatsBarProps) {
  if (loading) {
    return (
      <div
        data-testid={testId}
        style={{
          display: 'flex',
          alignItems: 'center',
          padding: '18px 24px',
          background: 'rgba(15,20,40,0.7)',
          border: '1px solid rgba(148,163,184,0.08)',
          borderRadius: 16,
          backdropFilter: 'blur(20px)',
          WebkitBackdropFilter: 'blur(20px)',
          gap: 16,
          marginBottom: 32,
        }}
      >
        {[1,2,3,4,5].map(i => (
          <div key={i} style={{ flex: 1, padding: '0 20px', borderLeft: i > 1 ? '1px solid rgba(255,255,255,0.05)' : 'none' }}>
            <Skeleton />
          </div>
        ))}
      </div>
    );
  }

  return (
    <div
      data-testid={testId}
      style={{
        display: 'flex',
        alignItems: 'center',
        padding: '18px 24px',
        background: 'linear-gradient(135deg, rgba(99,102,241,0.04), rgba(168,85,247,0.04))',
        border: '1px solid rgba(148,163,184,0.08)',
        borderRadius: 16,
        backdropFilter: 'blur(20px)',
        WebkitBackdropFilter: 'blur(20px)',
        marginBottom: 32,
      }}
    >
      {stats.map((s, i) => (
        <div
          key={i}
          style={{
            flex: 1,
            padding: '0 20px',
            borderLeft: i > 0 ? '1px solid rgba(255,255,255,0.05)' : 'none',
          }}
        >
          <p style={{
            fontSize: 12,
            color: '#64748b',
            textTransform: 'uppercase',
            letterSpacing: '0.08em',
            margin: '0 0 4px',
          }}>
            {s.label}
          </p>
          <p style={{
            fontSize: 24,
            fontWeight: 700,
            color: '#f8fafc',
            margin: 0,
            fontVariantNumeric: 'tabular-nums',
            letterSpacing: '-0.04em',
          }}>
            {s.value}
            {s.unit && <span style={{ fontSize: 14, color: '#64748b' }}>{s.unit}</span>}
          </p>
          {s.trendValue && (
            <p style={{
              fontSize: 12,
              color: TREND_COLOR_MAP[s.trendColor ?? 'gray'],
              margin: '2px 0 0',
            }}>
              {s.trendArrow ?? ''} {s.trendValue}
            </p>
          )}
        </div>
      ))}
    </div>
  );
}

export default StatsBar;