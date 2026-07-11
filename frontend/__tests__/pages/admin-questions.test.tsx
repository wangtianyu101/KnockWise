/**
 * 5 个新路由壳烟雾测试 — V3.8 P3b
 */
import { describe, it, expect, vi } from 'vitest';
import { render, screen } from '@testing-library/react';

vi.mock('next/router', () => ({
  useRouter: () => ({ push: vi.fn(), pathname: '/', query: {}, asPath: '/' }),
}));

import AdminQuestionsPage from '@/pages/admin/questions';
import AdminSyncPage from '@/pages/admin/sync';
import AiTodayPage from '@/pages/ai/today';
import AiHistoryPage from '@/pages/ai/history';
import SettingsPage from '@/pages/settings';

describe('5 新路由壳 · V3.8 P3b', () => {
  it('/admin/questions 显示 EmptyState', () => {
    render(<AdminQuestionsPage />);
    expect(screen.getByText(/题库管理 · 即将上线/)).toBeInTheDocument();
    expect(screen.getByText('🆕 ADMIN')).toBeInTheDocument();
  });

  it('/admin/sync 显示 EmptyState', () => {
    render(<AdminSyncPage />);
    expect(screen.getByText(/手动同步 · 即将上线/)).toBeInTheDocument();
  });

  it('/ai/today 显示 EmptyState', () => {
    render(<AiTodayPage />);
    expect(screen.getAllByText(/AI 今日推荐/).length).toBeGreaterThanOrEqual(1);
    expect(screen.getByText(/查看 Dashboard AI 卡/)).toBeInTheDocument();
  });

  it('/ai/history 显示 EmptyState', () => {
    render(<AiHistoryPage />);
    expect(screen.getAllByText(/推送历史/).length).toBeGreaterThanOrEqual(1);
  });

  it('/settings 显示 EmptyState', () => {
    render(<SettingsPage />);
    expect(screen.getAllByText(/设置/).length).toBeGreaterThanOrEqual(1);
    expect(screen.getAllByText(/用户偏好/).length).toBeGreaterThanOrEqual(1);
  });
});