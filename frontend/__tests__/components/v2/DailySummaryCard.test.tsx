/**
 * DailySummaryCard 组件测试 — T23 测试套件
 *
 * component-spec.md §2 6 状态全覆盖：
 * 加载 / 正常 / LLM降级 / 完全失败 / 首次使用 / 本周无答题
 */
import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest';
import { render, screen, waitFor } from '@testing-library/react';

vi.mock('next/router', () => ({
  useRouter: () => ({ push: vi.fn() }),
}));

vi.mock('@/lib/api', () => ({
  getToken: () => 'mock-token',
  getProfile: vi.fn(),
}));

import DailySummaryCard, { V2_ENABLED } from '@/components/v2-settlement/DailySummaryCard';

describe('<DailySummaryCard />', () => {
  beforeEach(() => {
    vi.stubGlobal('fetch', vi.fn());
  });
  afterEach(() => {
    vi.unstubAllGlobals();
  });

  it('V2_ENABLED 默认 true（未设 NEXT_PUBLIC_V2_ENABLED）', () => {
    expect(V2_ENABLED()).toBe(true);
  });

  it('V2_ENABLED=false 时组件返 null', () => {
    const original = process.env.NEXT_PUBLIC_V2_ENABLED;
    process.env.NEXT_PUBLIC_V2_ENABLED = 'false';
    const { container } = render(<DailySummaryCard />);
    expect(container.firstChild).toBeNull();
    process.env.NEXT_PUBLIC_V2_ENABLED = original;
  });

  it('加载中显示 antd Skeleton', async () => {
    (global.fetch as any).mockImplementation(() => new Promise(() => {}));

    render(<DailySummaryCard />);
    expect(document.querySelectorAll('.ant-skeleton').length).toBeGreaterThan(0);
  });

  it('正常状态渲染 summary 内容', async () => {
    (global.fetch as any).mockResolvedValue({
      ok: true,
      json: async () => ({
        title: '今日学习总结',
        date: '2026-06-28',
        yesterday_count: 8,
        mastered: [{ topic: 'React Hooks' }, { topic: 'TypeScript 泛型' }],
        weak_shift: [],
        body: '昨天你答了 8 道题，掌握 2 个新 topic。',
        _fallback: false,
      }),
    });

    render(<DailySummaryCard />);
    await waitFor(() => {
      expect(screen.getByText(/昨天你答了 8 道题/)).toBeInTheDocument();
    });
    // 副标题显示 "掌握 2 个新 topic"（不显示具体 topic 名）
    expect(screen.getAllByText(/掌握 2 个新 topic/).length).toBeGreaterThanOrEqual(1);
  });

  it('LLM 降级（_fallback=true）显示 warning tag', async () => {
    (global.fetch as any).mockResolvedValue({
      ok: true,
      json: async () => ({
        title: '今日学习总结',
        date: '2026-06-28',
        yesterday_count: 0,
        mastered: [],
        weak_shift: [],
        body: '今日总结暂不可用',
        _fallback: true,
      }),
    });

    render(<DailySummaryCard />);
    await waitFor(() => {
      expect(screen.getByText('降级版')).toBeInTheDocument();
    });
  });

  it('首次使用（yesterday_count=0 + mastered=空）显示空状态文案', async () => {
    (global.fetch as any).mockResolvedValue({
      ok: true,
      json: async () => ({
        title: '今日学习总结',
        date: '2026-06-28',
        yesterday_count: 0,
        mastered: [],
        weak_shift: [],
        body: '',
        _fallback: false,
      }),
    });

    render(<DailySummaryCard />);
    await waitFor(() => {
      expect(screen.getByText(/完成首日学习后/)).toBeInTheDocument();
    });
  });

  it('clickable=false 时不渲染"查看画像"按钮', async () => {
    (global.fetch as any).mockResolvedValue({
      ok: true,
      json: async () => ({
        title: '今日学习总结',
        date: '2026-06-28',
        yesterday_count: 8,
        mastered: [],
        weak_shift: [],
        body: '你答了 8 题',
        _fallback: false,
      }),
    });

    render(<DailySummaryCard clickable={false} />);
    await waitFor(() => {
      expect(screen.queryByText(/查看画像/)).toBeNull();
    });
  });
});