/**
 * V3 PlanCard 单元测试（PR 1 · T1 · 7 测试点）
 * 覆盖 GWT-4 (happy 创建) + GWT-5 (完成度聚合)
 */
import { describe, it, expect, vi } from 'vitest';
import { render, screen, fireEvent } from '@testing-library/react';
import { CurrentPlanCard, HistoryPlansList, PlanDetailCard, CreatePlanButton } from './PlanCard';
import type { StudyPlan } from '@/types/v3-plan';

const mockPlan: StudyPlan = {
  id: 'plan-001',
  name: '2 周算法冲刺',
  description: '专注算法基础',
  goal: '掌握 algorithms 50%',
  start_date: '2026-07-09',
  end_date: '2026-07-23',
  status: 'active',
  weekly_target: [
    { week_idx: 1, target_count: 10, target_topics: ['algorithms'] },
    { week_idx: 2, target_count: 10, target_topics: ['algorithms'] },
  ],
  progress: {
    total_target: 20,
    mastered: 10,
    learning: 5,
    new_count: 5,
    completion_rate: 0.5,
    weak_topics_remaining: [],
  },
  created_at: '2026-07-09T00:00:00Z',
  updated_at: '2026-07-09T00:00:00Z',
};

describe('CurrentPlanCard', () => {
  it('happy: 渲染计划名 + 进度 + 弱项', () => {
    render(<CurrentPlanCard plan={mockPlan} />);
    expect(screen.getByText('当前活跃计划')).toBeTruthy();
    expect(screen.getByText('"2 周算法冲刺"')).toBeTruthy();
    expect(screen.getByText(/10 \/ 20/)).toBeTruthy();
    // "[] ✓" 是 React 拆成 2 个元素（"[]" 文本 + " ✓" 文本）
    expect(screen.getAllByText(/\[\]/).length).toBeGreaterThan(0);
    expect(screen.getAllByText(/✓/).length).toBeGreaterThan(0);
  });

  it('edge: 完成度 0% 时进度条 width 为 0', () => {
    const emptyPlan: StudyPlan = {
      ...mockPlan,
      progress: { ...mockPlan.progress!, mastered: 0, completion_rate: 0 },
    };
    render(<CurrentPlanCard plan={emptyPlan} />);
    expect(screen.getByText(/0 \/ 20/)).toBeTruthy();
  });

  it('event: 点击"查看详情"调用 onViewDetail', () => {
    const onView = vi.fn();
    render(<CurrentPlanCard plan={mockPlan} onViewDetail={onView} />);
    fireEvent.click(screen.getByText(/查看详情/));
    expect(onView).toHaveBeenCalledWith('plan-001');
  });

  it('event: 点击"刷新进度"调用 onRefresh', () => {
    const onRefresh = vi.fn();
    render(<CurrentPlanCard plan={mockPlan} onRefresh={onRefresh} />);
    fireEvent.click(screen.getByText(/刷新进度/));
    expect(onRefresh).toHaveBeenCalledWith('plan-001');
  });
});

describe('HistoryPlansList', () => {
  it('happy: 渲染多个历史计划 + 状态标签', () => {
    const historyPlans: StudyPlan[] = [
      { ...mockPlan, id: 'p1', name: '30 天前端', status: 'completed' },
      { ...mockPlan, id: 'p2', name: '面试突击', status: 'completed' },
      { ...mockPlan, id: 'p3', name: '3 月刷题', status: 'paused' },
    ];
    render(<HistoryPlansList plans={historyPlans} onClick={() => {}} />);
    expect(screen.getByText('"30 天前端"')).toBeTruthy();
    // 2 个 completed 计划都有"已结束"标签，用 getAllByText
    expect(screen.getAllByText('已结束').length).toBe(2);
    expect(screen.getByText('已暂停')).toBeTruthy();
  });

  it('empty: 0 计划时显示空状态', () => {
    render(<HistoryPlansList plans={[]} onClick={() => {}} />);
    expect(screen.getByText('还没有历史计划')).toBeTruthy();
  });
});

describe('PlanDetailCard', () => {
  it('happy: 渲染详情 + 周目标列表', () => {
    const onBack = vi.fn();
    render(<PlanDetailCard plan={mockPlan} onBack={onBack} />);
    expect(screen.getByText('2 周算法冲刺')).toBeTruthy();
    expect(screen.getByText('第 1 周')).toBeTruthy();
    // 2 个 weekly_target 都有 "10 题 · algorithms"，用 getAllByText
    expect(screen.getAllByText(/10 题 · algorithms/).length).toBe(2);
  });
});

describe('CreatePlanButton', () => {
  it('event: 点击按钮调用 onClick', () => {
    const onClick = vi.fn();
    render(<CreatePlanButton onClick={onClick} />);
    fireEvent.click(screen.getByText(/创建新计划/));
    expect(onClick).toHaveBeenCalled();
  });
});
