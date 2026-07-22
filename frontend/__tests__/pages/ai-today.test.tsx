import { fireEvent, render, screen } from '@testing-library/react';
import { beforeEach, describe, expect, it, vi } from 'vitest';

const mocks = vi.hoisted(() => ({
  addBookmark: vi.fn(),
  hideItem: vi.fn(),
}));

vi.mock('next/router', () => ({
  useRouter: () => ({ push: vi.fn() }),
}));

vi.mock('@/hooks/useDigest', () => ({
  useDigestToday: () => ({
    data: {
      date: '2026-07-22',
      vibe: '今日 2 条',
      item_count: 2,
      items: [
        {
          id: 'item-1', rank: 1, title: 'Agent release', summary: 'Summary 1',
          quality_score: 0.91, type: 'model', region: 'overseas', category: 'headline',
          source_name: 'Example', source_url: 'https://example.com/1', published_at: null,
          estimated_minutes: 3, is_read: false, is_bookmarked: false, related_item_ids: [],
        },
        {
          id: 'item-2', rank: 2, title: '应用更新', summary: 'Summary 2',
          quality_score: 0.88, type: 'application', region: 'domestic', category: 'engineering',
          source_name: 'Fixture', source_url: 'https://example.com/2', published_at: null,
          estimated_minutes: 2, is_read: false, is_bookmarked: false, related_item_ids: [],
        },
      ],
    },
    isLoading: false,
    error: null,
    refetch: vi.fn(),
  }),
  useAddBookmark: () => ({ mutate: mocks.addBookmark }),
  useHideItem: () => ({ mutate: mocks.hideItem }),
}));

import AiTodayPage from '@/pages/ai/today';

describe('/ai/today', () => {
  beforeEach(() => vi.clearAllMocks());

  it('renders API items and supports bookmark and hide interactions', () => {
    render(<AiTodayPage />);

    expect(document.querySelectorAll('.digest-card')).toHaveLength(2);
    expect(document.querySelector('.vibe-badge')).toHaveTextContent('今日 2 条');

    fireEvent.click(screen.getAllByTitle('收藏')[0]);
    expect(mocks.addBookmark).toHaveBeenCalledWith('item-1');
    expect(screen.getByTitle('已收藏')).toBeInTheDocument();

    fireEvent.click(screen.getAllByTitle('屏蔽')[0]);
    expect(screen.getByText('不再推送类似内容？')).toBeInTheDocument();
  });
});
