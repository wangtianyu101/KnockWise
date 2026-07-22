/**
 * StatsBar 测试 — V3.8 P2 · 6 测试
 */
import { describe, it, expect, vi } from 'vitest';
import { render, screen } from '@testing-library/react';
import { StatsBar, type StatsBarStat } from '@/components/v3/StatsBar/StatsBar';

const TEST_STATS: StatsBarStat[] = [
  { label: '本周答题', value: 28, trend: 'up', trendValue: '+12%', trendColor: 'emerald', trendArrow: '↑' },
  { label: '命中率', value: '82', unit: '%', trend: 'up', trendValue: '+5pp', trendColor: 'emerald', trendArrow: '↑' },
  { label: '待复习', value: 14, trendValue: '3 题紧急', trendColor: 'amber' },
  { label: '连续打卡', value: 7, unit: '天', trendValue: '个人最佳', trendColor: 'amber' },
  { label: '已完成', value: '56/200', trendValue: '28% · 详情 →', trendColor: 'gray' },
];

describe('<StatsBar />', () => {
  it('渲染 5 列（label + value + trend）', () => {
    render(<StatsBar stats={TEST_STATS} />);
    expect(screen.getByText('本周答题')).toBeInTheDocument();
    expect(screen.getByText('命中率')).toBeInTheDocument();
    expect(screen.getByText('待复习')).toBeInTheDocument();
    expect(screen.getByText('连续打卡')).toBeInTheDocument();
    expect(screen.getByText('已完成')).toBeInTheDocument();
    expect(screen.getByText('28')).toBeInTheDocument();
    // value + unit 在两个 span，用 function matcher
    expect(screen.getByText((_, el) => el?.textContent === '82%')).toBeInTheDocument();
    expect(screen.getByText((_, el) => el?.textContent === '7天')).toBeInTheDocument();
  });

  it('value 数字等宽（tabular-nums）', () => {
    const { container } = render(<StatsBar stats={TEST_STATS} />);
    const valueEls = container.querySelectorAll('[style*="tabular-nums"]');
    expect(valueEls.length).toBeGreaterThanOrEqual(1);
  });

  it('emerald 趋势显示 +12%', () => {
    render(<StatsBar stats={TEST_STATS} />);
    // trendArrow + 空格 + trendValue
    expect(screen.getByText((_, el) => el?.textContent?.trim() === '↑ +12%')).toBeInTheDocument();
  });

  it('amber 趋势（3 题紧急）显示', () => {
    render(<StatsBar stats={TEST_STATS} />);
    expect(screen.getByText('3 题紧急')).toBeInTheDocument();
  });

  it('gray 趋势（28% · 详情 →）显示', () => {
    render(<StatsBar stats={TEST_STATS} />);
    expect(screen.getByText((_, el) => el?.textContent?.trim() === '28% · 详情 →')).toBeInTheDocument();
  });

  it('loading 状态显示 5 个 skeleton', () => {
    const { container } = render(<StatsBar stats={TEST_STATS} loading />);
    const skeletons = container.querySelectorAll('.skeleton');
    expect(skeletons.length).toBe(5);
  });
});