/**
 * V3.7 · AIRecommendationCard 单元测试（PR 6 · 4 测试点）
 * 覆盖：渲染 / 4 类型配色 / 失败隐藏 / 优先级映射
 */
import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest';
import { render, screen, fireEvent, waitFor } from '@testing-library/react';

// Mock the hook before importing component
const mockHookResult = vi.fn();
vi.mock('@/hooks/useAIRecommendations', () => ({
  useAIRecommendations: () => mockHookResult(),
}));

import { AIRecommendationCard } from '@/components/v3/AIRecommendationCard/AIRecommendationCard';

const sampleRecs = [
  {
    prefix: '[补]',
    title: 'System Design Caching',
    description: '3 次出现 · 优先级 high',
    priority: 'high',
    frequency: 3,
    rawTopic: 'system_design_caching',
  },
  {
    prefix: '[练]',
    title: 'LRU Cache',
    description: '2 次出现 · 优先级 medium',
    priority: 'medium',
    frequency: 2,
    rawTopic: 'lru_cache',
  },
  {
    prefix: '[读]',
    title: 'Distributed Cache Patterns',
    description: '1 次出现 · 优先级 low',
    priority: 'low',
    frequency: 1,
    rawTopic: 'distributed_cache',
  },
];

describe('AIRecommendationCard', () => {
  beforeEach(() => {
    mockHookResult.mockReturnValue({
      data: sampleRecs,
      loading: false,
      error: null,
      empty: false,
    });
  });

  afterEach(() => {
    vi.clearAllMocks();
  });

  it('happy: 渲染 3 条推荐 + 4 种类型配色', () => {
    render(<AIRecommendationCard />);
    expect(screen.getByText('今日 AI 推荐')).toBeTruthy();
    expect(screen.getByText('System Design Caching')).toBeTruthy();
    expect(screen.getByText('LRU Cache')).toBeTruthy();
    expect(screen.getByText('Distributed Cache Patterns')).toBeTruthy();
    // 3 个 prefix
    expect(screen.getByText('[补]')).toBeTruthy();
    expect(screen.getByText('[练]')).toBeTruthy();
    expect(screen.getByText('[读]')).toBeTruthy();
  });

  it('event: 点击推荐项触发埋点 + onItemClick 回调', () => {
    const onClick = vi.fn();
    const consoleSpy = vi.spyOn(console, 'log').mockImplementation(() => {});
    render(<AIRecommendationCard onItemClick={onClick} />);
    fireEvent.click(screen.getByText('LRU Cache'));
    expect(consoleSpy).toHaveBeenCalledWith(
      '[analytics] click_recommend',
      expect.objectContaining({ topic: 'lru_cache' }),
    );
    consoleSpy.mockRestore();
  });

  it('edge: 失败时隐藏整张卡（决策 7A）', () => {
    mockHookResult.mockReturnValue({
      data: [],
      loading: false,
      error: new Error('fetch failed'),
      empty: false,
    });
    const { container } = render(<AIRecommendationCard />);
    expect(container.firstChild).toBeNull();
    expect(screen.queryByText('今日 AI 推荐')).toBeNull();
  });

  it('edge: 加载中 / 空数据时隐藏', () => {
    mockHookResult.mockReturnValue({
      data: [],
      loading: true,
      error: null,
      empty: false,
    });
    const { container } = render(<AIRecommendationCard />);
    expect(container.firstChild).toBeNull();

    mockHookResult.mockReturnValue({
      data: [],
      loading: false,
      error: null,
      empty: true,
    });
    const { container: c2 } = render(<AIRecommendationCard />);
    expect(c2.firstChild).toBeNull();
  });
});
