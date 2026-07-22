/**
 * RadarMini 组件 — V3.8 P2
 *
 * 80×80 SVG · 5 维迷你雷达（spec §3.3 · design-spec §3.3）
 */
import React from 'react';
import { RADAR_DIMENSIONS, type InterviewRadarData } from '@/types/interview';

export type RadarColor = 'pink' | 'violet' | 'blue' | 'emerald' | 'amber';

export interface RadarMiniProps {
  data: InterviewRadarData;
  company?: string;
  score?: number;
  size?: number;
  color?: RadarColor;
  placeholder?: boolean;
  "data-testid"?: string;
}

const COLOR_HEX: Record<RadarColor, string> = {
  pink: '#f472b6',
  violet: '#a78bfa',
  blue: '#60a5fa',
  emerald: '#34d399',
  amber: '#fbbf24',
};

function hexToRgba(hex: string, alpha: number): string {
  const r = parseInt(hex.slice(1, 3), 16);
  const g = parseInt(hex.slice(3, 5), 16);
  const b = parseInt(hex.slice(5, 7), 16);
  return `rgba(${r},${g},${b},${alpha})`;
}

export function RadarMini({
  data,
  company,
  score,
  size = 80,
  color = 'pink',
  placeholder = false,
  'data-testid': testId = 'radar-mini',
}: RadarMiniProps) {
  const stroke = COLOR_HEX[color];

  // 5 边形外框（5 个顶点）
  const vertices = [
    { x: 40, y: 8 },
    { x: 70, y: 28 },
    { x: 60, y: 68 },
    { x: 20, y: 68 },
    { x: 10, y: 28 },
  ];
  const outlinePoints = vertices.map(v => `${v.x},${v.y}`).join(' ');

  // 检查 data 是否完全空（所有 dim 都 undefined）
  const hasData = RADAR_DIMENSIONS.some(dim => data[dim] !== undefined);

  if (placeholder || !hasData) {
    return (
      <div data-testid={testId} style={{ textAlign: 'center' }}>
        <svg viewBox="0 0 80 80" width={size} height={size} aria-hidden="true">
          <polygon
            points={outlinePoints}
            fill="none"
            stroke={placeholder ? "rgba(255,255,255,0.1)" : "rgba(148,163,184,0.08)"}
            strokeWidth="1"
            strokeDasharray={placeholder ? "3 3" : undefined}
          />
        </svg>
        {company && <p style={{ fontSize: 12, color: '#64748b', margin: '4px 0 0' }}>{company}</p>}
        {score !== undefined && <p style={{ fontSize: 12, color: '#64748b', margin: '4px 0 0', fontVariantNumeric: 'tabular-nums' }}>{score}</p>}
      </div>
    );
  }

  // 数据多边形（5 维值 → 缩放后的点）
  const dataPoints = vertices.map((v, i) => {
    const dim = RADAR_DIMENSIONS[i];
    const value = data[dim] ?? 0;
    const ratio = Math.min(1, Math.max(0, value / 100));
    return {
      x: 40 + (v.x - 40) * ratio,
      y: 40 + (v.y - 40) * ratio,
    };
  });
  const polygonPoints = dataPoints.map(p => `${p.x},${p.y}`).join(' ');

  return (
    <div data-testid={testId} style={{ textAlign: 'center' }}>
      <svg viewBox="0 0 80 80" width={size} height={size} aria-hidden="true">
        <polygon
          points={outlinePoints}
          fill="none"
          stroke={hexToRgba(stroke, 0.15)}
          strokeWidth="1"
        />
        <polygon
          points={polygonPoints}
          fill={hexToRgba(stroke, 0.25)}
          stroke={stroke}
          strokeWidth="1.5"
        />
      </svg>
      {score !== undefined && (
        <p style={{ fontSize: 12, color: '#94a3b8', margin: '4px 0 0', fontVariantNumeric: 'tabular-nums' }}>
          {score}
        </p>
      )}
      {company && <p style={{ fontSize: 12, color: '#64748b', margin: 0 }}>{company}</p>}
    </div>
  );
}

export default RadarMini;