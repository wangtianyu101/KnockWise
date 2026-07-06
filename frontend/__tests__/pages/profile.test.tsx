/**
 * ProfilePage (/profile) 组件测试 — T25 测试套件
 */
import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest';
import { render, screen, waitFor } from '@testing-library/react';

vi.mock('next/router', () => ({
  useRouter: () => ({ push: vi.fn() }),
}));
vi.mock('@/lib/api', () => ({
  getToken: () => 'mock-token',
  getProfile: vi.fn().mockResolvedValue({
    user_id: 'u-1',
    display_name: '测试用户',
    weak_topics: [],
    mastered_topics: [],
    learning_trajectory: {},
    last_active_at: null,
  }),
}));

import ProfilePage from '@/pages/profile';

describe('<ProfilePage />', () => {
  beforeEach(() => {
    vi.stubGlobal('fetch', vi.fn());
  });
  afterEach(() => {
    vi.unstubAllGlobals();
  });

  it('加载中显示 antd Spin', () => {
    (global.fetch as any).mockImplementation(() => new Promise(() => {}));
    render(<ProfilePage />);
    expect(document.querySelector('.ant-spin')).toBeTruthy();
  });

  it('空状态显示 Empty 组件（无弱项）', async () => {
    (global.fetch as any).mockResolvedValue({
      ok: true,
      json: async () => null,
    });

    render(<ProfilePage />);
    await waitFor(() => {
      expect(
        screen.getByText(/答 3 道题后这里会出现你的成长轨迹/),
      ).toBeInTheDocument();
    });
  });

  it('有数据时显示 4 个 Stat 卡', async () => {
    const getProfileMock = await import('@/lib/api');
    vi.mocked(getProfileMock.getProfile).mockResolvedValueOnce({
      user_id: 'u-1',
      display_name: 'Test',
      weak_topics: [{ topic: '网络层', error_rate: 0.6, practice_count: 3, last_practiced_at: '2026-06-20T00:00:00Z', related_question_ids: [] }],
      mastered_topics: [{ topic: 'React Hooks', error_rate: 0.0, practice_count: 5, last_practiced_at: '2026-06-22T00:00:00Z', related_question_ids: [] }],
      learning_trajectory: {},
      last_active_at: '2026-06-28T00:00:00Z',
    } as any);

    (global.fetch as any).mockResolvedValue({
      ok: true,
      json: async () => null,
    });

    render(<ProfilePage />);
    await waitFor(() => {
      expect(screen.getByText(/我的画像/)).toBeInTheDocument();
    });
    // 至少 4 张 Stat 卡
    expect(document.querySelectorAll('.ant-statistic').length).toBeGreaterThanOrEqual(4);
  });

  it('学习趋势数据 < 2 周显示"继续学习 2 周后看到趋势"', async () => {
    (global.fetch as any).mockResolvedValue({
      ok: true,
      json: async () => ({
        week: '2026-W26',
        total_questions: 5,
        mastered_count: 1,
        weak_topics: [],
        body: '',
        trajectory: { '2026-W26': { mastered_count: 1 } },
      }),
    });

    render(<ProfilePage />);
    await waitFor(() => {
      expect(screen.getByText(/继续学习 2 周后看到趋势/)).toBeInTheDocument();
    });
  });
});