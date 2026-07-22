/**
 * HeroCard 5 状态测试 — V3.8 P2
 *
 * 覆盖 5 状态视觉区分 + 回调 + 自动 state 判定
 * 合计：7 测试
 */
import { describe, it, expect, vi } from 'vitest';
import { render, screen, fireEvent } from '@testing-library/react';

vi.mock('next/router', () => ({
  useRouter: () => ({ push: vi.fn(), pathname: '/dashboard', query: {}, asPath: '/dashboard' }),
}));

import { HeroCard, type HeroState } from '@/components/v3/HeroCard/HeroCard';
import type { InterviewRecentItem } from '@/types/interview';

const MOCK_RECENT: InterviewRecentItem[] = [
  {
    id: '1',
    round: '字节·后端',
    style: 'tech',
    status: 'completed',
    total_questions: 8,
    overall_score: 78,
    radar_data: { algorithm: 78, system_design: 75, network: 65, frontend: 50, ai: 40 },
    started_at: '2026-07-08T14:30:00Z',
    ended_at: '2026-07-08T15:05:00Z',
  },
];

describe('<HeroCard />', () => {
  describe('5 状态视觉', () => {
    it('full 状态：显示 3 雷达 + 上次成绩 + 主按钮', () => {
      const recent = Array(3).fill(MOCK_RECENT[0]).map((r, i) => ({ ...r, id: String(i) }));
      const { container } = render(
        <HeroCard
          lastInterview={recent[0]}
          recentInterviews={recent}
          totalInterviews={12}
          avgScore={72}
          onStartInterview={vi.fn()}
        />
      );
      // 3 雷达 = container 内 ≥3 个 svg
      const radars = container.querySelectorAll('svg');
      expect(radars.length).toBeGreaterThanOrEqual(3);
      // 主按钮
      expect(screen.getByText(/^开始面试/)).toBeInTheDocument();
      // 上次成绩 78（多处出现都行）
      expect(screen.getAllByText('78').length).toBeGreaterThanOrEqual(1);
    });

    it('partial 状态：显示 1 雷达 + "再完成 X 次" CTA', () => {
      const recent = [MOCK_RECENT[0]];
      render(
        <HeroCard
          lastInterview={recent[0]}
          recentInterviews={recent}
          totalInterviews={5}
          avgScore={68}
          onStartInterview={vi.fn()}
        />
      );
      expect(screen.getByText(/再完成 2 次/)).toBeInTheDocument();
      expect(screen.getByText(/^开始第/)).toBeInTheDocument();
    });

    it('empty 状态：显示 EmptyState + "开始第一次面试" CTA', () => {
      render(
        <HeroCard
          recentInterviews={[]}
          totalInterviews={0}
          avgScore={null}
          onStartInterview={vi.fn()}
        />
      );
      expect(screen.getByText(/还没有面试记录/)).toBeInTheDocument();
      expect(screen.getByText(/开始第一次面试/)).toBeInTheDocument();
    });

    it('loading 状态：显示 skeleton（不可点击主按钮）', () => {
      render(
        <HeroCard
          recentInterviews={[]}
          totalInterviews={0}
          avgScore={null}
          loading={true}
          onStartInterview={vi.fn()}
        />
      );
      // skeleton 元素应存在（通过 data-testid 或 className）
      const skeletons = document.querySelectorAll('.skeleton, [data-testid*="skeleton"]');
      expect(skeletons.length).toBeGreaterThan(0);
    });

    it('error 状态：显示红色警告 + 重试 CTA', () => {
      render(
        <HeroCard
          recentInterviews={[]}
          totalInterviews={0}
          avgScore={null}
          state="error"
          onRetry={vi.fn()}
        />
      );
      expect(screen.getByText(/加载失败/)).toBeInTheDocument();
      expect(screen.getByText('重试')).toBeInTheDocument();
    });
  });

  describe('回调', () => {
    it('点击"开始面试"触发 onStartInterview', () => {
      const onStart = vi.fn();
      const recent = Array(3).fill(MOCK_RECENT[0]).map((r, i) => ({ ...r, id: String(i) }));
      render(
        <HeroCard
          lastInterview={recent[0]}
          recentInterviews={recent}
          totalInterviews={12}
          avgScore={72}
          onStartInterview={onStart}
        />
      );
      fireEvent.click(screen.getByText(/开始面试/));
      expect(onStart).toHaveBeenCalledTimes(1);
    });

    it('error 状态点击"重试"触发 onRetry', () => {
      const onRetry = vi.fn();
      render(
        <HeroCard
          recentInterviews={[]}
          totalInterviews={0}
          avgScore={null}
          state="error"
          onRetry={onRetry}
        />
      );
      fireEvent.click(screen.getByText('重试'));
      expect(onRetry).toHaveBeenCalledTimes(1);
    });
  });
});