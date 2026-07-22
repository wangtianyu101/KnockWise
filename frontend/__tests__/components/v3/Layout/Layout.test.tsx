/**
 * Layout + TopNav 组件测试 — V3.8 P1
 *
 * 覆盖：
 * - Layout 渲染 Sidebar + TopNav + main（1 测试）
 * - Layout currentPage 传递（1 测试）
 * - TopNav 极简：logo + breadcrumb + 用户菜单（1 测试）
 *
 * 合计：3 测试
 */
import { describe, it, expect, vi } from 'vitest';
import { render, screen, fireEvent } from '@testing-library/react';

vi.mock('next/router', () => ({
  useRouter: () => ({
    push: vi.fn(),
    replace: vi.fn(),
    pathname: '/dashboard',
    query: {},
    asPath: '/dashboard',
  }),
}));

import { Layout } from '@/components/v3/Layout/Layout';
import { TopNav } from '@/components/v3/TopNav/TopNav';

describe('<Layout />', () => {
  it('渲染 Sidebar + TopNav + main + children', () => {
    render(
      <Layout currentPage="/dashboard">
        <div data-testid="page-content">Hello</div>
      </Layout>
    );
    // Sidebar 存在
    expect(screen.getByTestId('sidebar')).toBeInTheDocument();
    // TopNav 存在
    expect(screen.getByTestId('topnav')).toBeInTheDocument();
    // main 存在
    expect(screen.getByRole('main')).toBeInTheDocument();
    // children 渲染
    expect(screen.getByTestId('page-content')).toBeInTheDocument();
    expect(screen.getByText('Hello')).toBeInTheDocument();
  });

  it('currentPage 传给 Sidebar（让对应菜单项 active）', () => {
    render(
      <Layout currentPage="/dashboard">
        <div>x</div>
      </Layout>
    );
    // dashboard 菜单项应有 active class
    const dashboardItem = screen.getByTestId('sidebar').querySelector('[data-page="/dashboard"]');
    expect(dashboardItem?.className).toContain('active');
  });

  it('main marginLeft 跟随 Sidebar 折叠（240 → 64）', () => {
    const { container, getByLabelText } = render(
      <Layout currentPage="/dashboard">
        <div>x</div>
      </Layout>
    );
    const main = container.querySelector<HTMLElement>('main[role="main"]')!;
    // 初始 240px
    expect(main.style.marginLeft).toBe('240px');

    // 点折叠按钮 → 64px
    fireEvent.click(getByLabelText('折叠侧栏'));
    expect(main.style.marginLeft).toBe('64px');

    // 再点（展开）→ 240px
    fireEvent.click(getByLabelText('展开侧栏'));
    expect(main.style.marginLeft).toBe('240px');
  });
});

describe('<TopNav />', () => {
  it('渲染 logo + brand + breadcrumb + 用户菜单', () => {
    render(<TopNav breadcrumb="今日概览" userName="开发者" />);
    // brand
    expect(screen.getByText('KnockWise')).toBeInTheDocument();
    // breadcrumb
    expect(screen.getByText('今日概览')).toBeInTheDocument();
    // 用户
    expect(screen.getByText('开发者')).toBeInTheDocument();
  });
});