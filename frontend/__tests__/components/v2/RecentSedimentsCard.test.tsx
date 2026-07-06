/**
 * RecentSedimentsCard 组件测试 — T24 测试套件
 */
import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest';
import { render, screen, waitFor } from '@testing-library/react';

vi.mock('next/router', () => ({ useRouter: () => ({ push: vi.fn() }) }));
vi.mock('@/lib/api', () => ({
  getToken: () => 'mock-token',
  getProfile: vi.fn(),
}));

import RecentSedimentsCard from '@/components/v2-settlement/RecentSedimentsCard';

describe('<RecentSedimentsCard />', () => {
  beforeEach(() => {
    vi.stubGlobal('fetch', vi.fn());
  });
  afterEach(() => {
    vi.unstubAllGlobals();
  });

  it('加载中显示 antd Spin', () => {
    (global.fetch as any).mockImplementation(() => new Promise(() => {}));
    render(<RecentSedimentsCard />);
    expect(document.querySelector('.ant-spin')).toBeTruthy();
  });

  it('空文件列表显示 Empty 组件', async () => {
    (global.fetch as any).mockResolvedValue({
      ok: true,
      json: async () => [],
    });

    render(<RecentSedimentsCard />);
    await waitFor(() => {
      expect(screen.getByText(/答完第一道题后/)).toBeInTheDocument();
    });
  });

  it('vault 不存在（full_path=null）显示 Alert 警告', async () => {
    (global.fetch as any).mockResolvedValue({
      ok: true,
      json: async () => [
        { rel_path: 'learning/2026-06-28.md', full_path: null, success: false, error: 'vault missing' },
      ],
    });

    render(<RecentSedimentsCard />);
    await waitFor(() => {
      expect(screen.getByText(/Obsidian 路径不存在/)).toBeInTheDocument();
    });
    expect(screen.getAllByText(/vault 不可用/i).length).toBeGreaterThan(0);
  });

  it('正常状态显示文件列表', async () => {
    (global.fetch as any).mockResolvedValue({
      ok: true,
      json: async () => [
        { rel_path: 'learning/2026-06-28.md', full_path: '/Users/x/Obsidian/coding/learning/2026-06-28.md', success: true, error: null },
        { rel_path: 'learning/2026-06-27.md', full_path: '/Users/x/Obsidian/coding/learning/2026-06-27.md', success: true, error: null },
      ],
    });

    render(<RecentSedimentsCard />);
    await waitFor(() => {
      expect(screen.getByText('learning/2026-06-28.md')).toBeInTheDocument();
    });
    expect(screen.getByText('learning/2026-06-27.md')).toBeInTheDocument();
  });

  it('limit prop 传给 fetch URL', async () => {
    const fetchMock = vi.fn().mockResolvedValue({
      ok: true,
      json: async () => [],
    });
    (global.fetch as any) = fetchMock;

    render(<RecentSedimentsCard limit={10} />);
    await waitFor(() => {
      expect(fetchMock).toHaveBeenCalledWith(
        expect.stringContaining('limit=10'),
        expect.any(Object),
      );
    });
  });
});