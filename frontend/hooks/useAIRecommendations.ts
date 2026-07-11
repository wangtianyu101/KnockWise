/**
 * V3.7 · useAIRecommendations hook（PR 6）
 * 调 V2 已实装的 /api/analytics/recommendations endpoint
 * 适配 V2 字段（topic/label/frequency/priority）→ V3.7 视觉
 */
import { useEffect, useState } from 'react';

export interface AIRecommendation {
  /** V3 内部字段（从 V2 字段映射）*/
  prefix: '[补]' | '[练]' | '[读]' | '[盘]';
  title: string;
  description: string;
  priority: 'high' | 'medium' | 'low';
  frequency: number;
  rawTopic: string;
}

const API_BASE = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';

function mapV2ToV3(raw: any): AIRecommendation {
  // V2 priority: high/medium/low → V3 prefix 配色
  const prefixMap: Record<string, AIRecommendation['prefix']> = {
    high: '[补]',
    medium: '[练]',
    low: '[读]',
  };
  return {
    prefix: prefixMap[raw.priority] || '[盘]',
    title: raw.label || raw.topic,
    description: `${raw.frequency || 0} 次出现 · 优先级 ${raw.priority || 'low'}`,
    priority: raw.priority || 'low',
    frequency: raw.frequency || 0,
    rawTopic: raw.topic,
  };
}

export function useAIRecommendations() {
  const [data, setData] = useState<AIRecommendation[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<Error | null>(null);
  const [empty, setEmpty] = useState(false);

  useEffect(() => {
    const token = typeof window !== 'undefined' ? localStorage.getItem('devbrain_token') : null;
    if (!token) {
      setLoading(false);
      setEmpty(true);
      return;
    }
    let cancelled = false;
    (async () => {
      try {
        const res = await fetch(`${API_BASE}/api/analytics/recommendations`, {
          headers: { Authorization: `Bearer ${token}` },
        });
        if (!res.ok) {
          throw new Error(`HTTP ${res.status}`);
        }
        const json = await res.json();
        if (cancelled) return;
        const recs = (json.recommendations || []).map(mapV2ToV3);
        setData(recs);
        setEmpty(recs.length === 0);
      } catch (e) {
        if (cancelled) return;
        setError(e as Error);
        setData([]);
      } finally {
        if (!cancelled) setLoading(false);
      }
    })();
    return () => {
      cancelled = true;
    };
  }, []);

  return { data, loading, error, empty };
}
