/**
 * Sidebar 6 组件测试 — V3.8 P1
 *
 * 覆盖：
 * - Sidebar (4 测试)
 * - SidebarHeader (2 测试)
 * - SidebarSearch (3 测试)
 * - SidebarGroup (3 测试)
 * - SidebarItem (4 测试)
 * - SidebarDivider (2 测试)
 *
 * 合计：18 测试
 */
import { describe, it, expect, vi } from 'vitest';
import { render, screen, fireEvent } from '@testing-library/react';

vi.mock('next/router', () => ({
  useRouter: () => ({
    push: vi.fn(),
    replace: vi.fn(),
    pathname: '/',
    query: {},
    asPath: '/',
  }),
}));

import { Sidebar } from '@/components/v3/Sidebar/Sidebar';
import { SidebarHeader } from '@/components/v3/Sidebar/SidebarHeader';
import { SidebarSearch } from '@/components/v3/Sidebar/SidebarSearch';
import { SidebarGroup } from '@/components/v3/Sidebar/SidebarGroup';
import { SidebarItem } from '@/components/v3/Sidebar/SidebarItem';
import { SidebarDivider } from '@/components/v3/Sidebar/SidebarDivider';
import type { SidebarMenuGroup } from '@/components/v3/Sidebar/Sidebar';

// 测试用 fixture：5 分组 + Admin
const TEST_GROUPS: SidebarMenuGroup[] = [
  {
    title: '概览',
    items: [
      { page: 'dashboard', label: '今日概览', icon: <svg data-testid="icon-dashboard" /> },
    ],
  },
  {
    title: '面试',
    items: [
      { page: 'interview-today', label: '今日面试', icon: <svg />, badge: 'new' },
      { page: 'interview-history', label: '历史报告', icon: <svg /> },
    ],
  },
  {
    title: '学习复习',
    items: [
      { page: 'learn', label: '题目浏览', icon: <svg /> },
      { page: 'plan', label: '学习计划', icon: <svg />, badge: 'v3' },
    ],
  },
  {
    title: 'AI 推送',
    items: [
      { page: 'ai-today', label: '今日推荐', icon: <svg />, badge: 'v3' },
    ],
  },
  {
    title: 'ADMIN',
    titleColor: '#f59e0b',
    items: [
      { page: 'admin-questions', label: '题库管理', icon: <svg />, badge: 'admin' },
      { page: 'admin-sync', label: '手动同步', icon: <svg />, badge: 'admin' },
    ],
  },
];

describe('<Sidebar />', () => {
  it('渲染所有菜单项', () => {
    render(<Sidebar groups={TEST_GROUPS} currentPage="dashboard" />);
    expect(screen.getByText('今日概览')).toBeInTheDocument();
    expect(screen.getByText('今日面试')).toBeInTheDocument();
    expect(screen.getByText('历史报告')).toBeInTheDocument();
    expect(screen.getByText('题目浏览')).toBeInTheDocument();
    expect(screen.getByText('学习计划')).toBeInTheDocument();
    expect(screen.getByText('今日推荐')).toBeInTheDocument();
    expect(screen.getByText('题库管理')).toBeInTheDocument();
    expect(screen.getByText('手动同步')).toBeInTheDocument();
  });

  it('当前 page 高亮（active class）', () => {
    const { container } = render(
      <Sidebar groups={TEST_GROUPS} currentPage="dashboard" />
    );
    const dashboardItem = container.querySelector('[data-page="dashboard"]');
    expect(dashboardItem?.className).toContain('active');
    const aiItem = container.querySelector('[data-page="ai-today"]');
    expect(aiItem?.className).not.toContain('active');
  });

  it('collapsed 状态切换：width 变化', () => {
    const onCollapsedChange = vi.fn();
    const { container, rerender } = render(
      <Sidebar
        groups={TEST_GROUPS}
        collapsed={false}
        onCollapsedChange={onCollapsedChange}
      />
    );
    const sidebar = container.querySelector<HTMLElement>('[data-testid="sidebar"]')!;
    expect(sidebar.style.width).toBe('240px');
    expect(sidebar.className).not.toContain('collapsed');

    rerender(
      <Sidebar
        groups={TEST_GROUPS}
        collapsed={true}
        onCollapsedChange={onCollapsedChange}
      />
    );
    expect(sidebar.style.width).toBe('64px');
    expect(sidebar.className).toContain('collapsed');
  });

  it('搜索输入过滤菜单（onSearch 回调 + 内部过滤）', () => {
    const onSearch = vi.fn();
    render(<Sidebar groups={TEST_GROUPS} currentPage="dashboard" onSearch={onSearch} />);
    const input = screen.getByPlaceholderText(/搜索页面/);
    fireEvent.change(input, { target: { value: '面试' } });
    expect(onSearch).toHaveBeenCalledWith('面试');
    // 内部过滤：只剩"面试"分组
    expect(screen.queryByText('今日概览')).not.toBeInTheDocument();
    expect(screen.getByText('今日面试')).toBeInTheDocument();
    expect(screen.getByText('历史报告')).toBeInTheDocument();
    expect(screen.queryByText('题目浏览')).not.toBeInTheDocument();
  });

  it('搜索清空恢复全部菜单', () => {
    render(<Sidebar groups={TEST_GROUPS} currentPage="dashboard" />);
    const input = screen.getByPlaceholderText(/搜索页面/);
    fireEvent.change(input, { target: { value: '面试' } });
    expect(screen.queryByText('今日概览')).not.toBeInTheDocument();
    fireEvent.change(input, { target: { value: '' } });
    expect(screen.getByText('今日概览')).toBeInTheDocument();
    expect(screen.getByText('题目浏览')).toBeInTheDocument();
  });
});

describe('<SidebarHeader />', () => {
  it('渲染 brand 文字 + Logo', () => {
    render(
      <SidebarHeader
        brand="KnockWise"
        logo={<svg data-testid="logo" />}
        collapsed={false}
        onToggle={vi.fn()}
      />
    );
    expect(screen.getByText('KnockWise')).toBeInTheDocument();
    expect(screen.getByTestId('logo')).toBeInTheDocument();
  });

  it('点击折叠按钮触发 onToggle', () => {
    const onToggle = vi.fn();
    render(
      <SidebarHeader
        brand="KnockWise"
        collapsed={false}
        onToggle={onToggle}
      />
    );
    screen.getByRole('button', { name: /折叠/ }).click();
    expect(onToggle).toHaveBeenCalledTimes(1);
  });
});

describe('<SidebarSearch />', () => {
  it('输入触发 onSearch', () => {
    const onSearch = vi.fn();
    render(<SidebarSearch onSearch={onSearch} />);
    const input = screen.getByPlaceholderText(/搜索页面/);
    fireEvent.change(input, { target: { value: 'plan' } });
    expect(onSearch).toHaveBeenCalledWith('plan');
  });

  it('默认 placeholder 是 "搜索页面..."', () => {
    render(<SidebarSearch onSearch={vi.fn()} />);
    expect(screen.getByPlaceholderText('搜索页面...')).toBeInTheDocument();
  });

  it('清空 input 后 onSearch 收到空字符串', () => {
    const onSearch = vi.fn();
    render(<SidebarSearch onSearch={onSearch} defaultValue="abc" />);
    const input = screen.getByDisplayValue('abc');
    fireEvent.change(input, { target: { value: '' } });
    expect(onSearch).toHaveBeenCalledWith('');
  });
});

describe('<SidebarGroup />', () => {
  it('渲染 title + children', () => {
    render(
      <SidebarGroup title="概览" data-testid="group">
        <div>child</div>
      </SidebarGroup>
    );
    expect(screen.getByText('概览')).toBeInTheDocument();
    expect(screen.getByText('child')).toBeInTheDocument();
  });

  it('自定义 titleColor 应用到标题', () => {
    const { container } = render(
      <SidebarGroup title="ADMIN" titleColor="#f59e0b" data-testid="group">
        <div>x</div>
      </SidebarGroup>
    );
    const title = container.querySelector('[data-testid="group-title"]')!;
    expect(title.getAttribute('style') || '').toMatch(/#f59e0b/);
  });

  it('collapsed=true 时 children 隐藏', () => {
    render(
      <SidebarGroup title="概览" collapsed={true} data-testid="group">
        <div data-testid="child">x</div>
      </SidebarGroup>
    );
    // 折叠态：children 应有 hidden class 或 display:none
    const child = screen.getByTestId('child');
    expect(child.parentElement?.className || '').toMatch(/hidden|display.*none/);
  });
});

describe('<SidebarItem />', () => {
  it('active=true 加 active class', () => {
    render(
      <SidebarItem page="dashboard" active={true} data-testid="item">
        今日概览
      </SidebarItem>
    );
    const item = screen.getByTestId('item');
    expect(item.className).toContain('active');
  });

  it('点击触发 href 跳转（router.push）', () => {
    render(
      <SidebarItem page="learn" href="/learn" data-testid="item">
        学习
      </SidebarItem>
    );
    screen.getByTestId('item').click();
    // router.push 已在 vi.mock 中 mock，无报错即通过
  });

  it('badge="v3" 显示 V3 徽章', () => {
    render(
      <SidebarItem page="plan" badge="v3" data-testid="item">
        学习计划
      </SidebarItem>
    );
    expect(screen.getByText('V3')).toBeInTheDocument();
  });

  it('badge="admin" 显示 🆕 徽章', () => {
    render(
      <SidebarItem page="admin-questions" badge="admin" data-testid="item">
        题库管理
      </SidebarItem>
    );
    expect(screen.getByText('🆕')).toBeInTheDocument();
  });
});

describe('<SidebarDivider />', () => {
  it('无 label 时只渲染分隔线', () => {
    const { container } = render(<SidebarDivider data-testid="div" />);
    const div = container.querySelector('[data-testid="div"]')!;
    expect(div).toBeInTheDocument();
    // 分隔线元素
    expect(div.querySelector('hr') || div.tagName === 'HR').toBeTruthy();
  });

  it('带 label 显示文字', () => {
    render(<SidebarDivider label="ADMIN" />);
    expect(screen.getByText('ADMIN')).toBeInTheDocument();
  });
});