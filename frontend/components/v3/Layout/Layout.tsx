/**
 * Layout — V3.8 P1 全局布局
 *
 * 注入 Sidebar + TopNav + main content area
 *
 * 16 page Sidebar 菜单配置（V3.6 已锁定的 5 大分组 + Admin · 与 v3-mockup.html 一致）
 */
import React, { useState, useEffect } from 'react';
import { Sidebar, type SidebarMenuGroup } from '../Sidebar/Sidebar';
import { TopNav } from '../TopNav/TopNav';

// KnockWise Logo SVG（候选 A：敲门图标）
const KW_LOGO = (
  <svg width="22" height="22" viewBox="0 0 28 28" fill="none">
    <defs>
      <linearGradient id="logo-grad-sidebar" x1="0" y1="0" x2="28" y2="28">
        <stop stopColor="#6366f1" />
        <stop offset="1" stopColor="#a78bfa" />
      </linearGradient>
    </defs>
    <rect x="2" y="2" width="24" height="24" rx="7" fill="url(#logo-grad-sidebar)" />
    <path d="M10 8L10 20M10 20L13 17M10 20L13 23"
      stroke="white" strokeWidth="2" strokeLinecap="round" />
    <path d="M17 11L17 17M17 17L20 14M17 17L20 20"
      stroke="white" strokeWidth="2" strokeLinecap="round" opacity="0.5" />
  </svg>
);

const ICON = {
  dashboard: (
    <svg width="16" height="16" viewBox="0 0 16 16" fill="none">
      <rect x="2" y="2" width="5" height="5" rx="1" stroke="currentColor" strokeWidth="1.5" />
      <rect x="9" y="2" width="5" height="5" rx="1" stroke="currentColor" strokeWidth="1.5" />
      <rect x="2" y="9" width="5" height="5" rx="1" stroke="currentColor" strokeWidth="1.5" />
      <rect x="9" y="9" width="5" height="5" rx="1" stroke="currentColor" strokeWidth="1.5" />
    </svg>
  ),
  interview: (
    <svg width="16" height="16" viewBox="0 0 16 16" fill="none">
      <circle cx="8" cy="8" r="6.5" stroke="currentColor" strokeWidth="1.3" />
      <path d="M8 4V8L10.5 9.5" stroke="currentColor" strokeWidth="1.3" strokeLinecap="round" />
    </svg>
  ),
  learn: (
    <svg width="16" height="16" viewBox="0 0 16 16" fill="none">
      <path d="M2 4C2 3.45 2.45 3 3 3H13C13.55 3 14 3.45 14 4V13L8 11L2 13V4Z"
        stroke="currentColor" strokeWidth="1.3" strokeLinejoin="round" />
    </svg>
  ),
  plan: (
    <svg width="16" height="16" viewBox="0 0 16 16" fill="none">
      <path d="M5 1.5L10 3.5L5 5.5V1.5Z" fill="currentColor" />
      <path d="M10 3.5V8.5L5 11V5.5L10 3.5Z" stroke="currentColor" strokeWidth="1.3" />
    </svg>
  ),
  collections: (
    <svg width="16" height="16" viewBox="0 0 16 16" fill="none">
      <path d="M2 3.5L8 1.5L14 3.5L8 5.5L2 3.5Z" stroke="currentColor" strokeWidth="1.3" strokeLinejoin="round" />
      <path d="M2 7.5L8 9.5L14 7.5" stroke="currentColor" strokeWidth="1.3" />
      <path d="M2 11.5L8 13.5L14 11.5" stroke="currentColor" strokeWidth="1.3" />
    </svg>
  ),
  knowledge: (
    <svg width="16" height="16" viewBox="0 0 16 16" fill="none">
      <path d="M2 2C2 1.45 2.45 1 3 1H5L6.5 2.5H9C9.55 2.5 10 2.95 10 3.5V9.5C10 10.05 9.55 10.5 9 10.5H3C2.45 10.5 2 10.05 2 9.5V2Z"
        stroke="currentColor" strokeWidth="1.3" />
    </svg>
  ),
  qa: (
    <svg width="16" height="16" viewBox="0 0 16 16" fill="none">
      <path d="M2 4C2 2.9 2.9 2 4 2H12C13.1 2 14 2.9 14 4V10C14 11.1 13.1 12 12 12H6L3 14.5V12H4C2.9 12 2 11.1 2 10V4Z"
        stroke="currentColor" strokeWidth="1.3" strokeLinejoin="round" />
    </svg>
  ),
  report: (
    <svg width="16" height="16" viewBox="0 0 16 16" fill="none">
      <path d="M3 13V7M7 13V3M11 13V9" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" />
    </svg>
  ),
  ai: (
    <svg width="16" height="16" viewBox="0 0 16 16" fill="none">
      <path d="M6 1L6.6 4L9 4.5L6.6 5L6 8L5.4 5L3 4.5L5.4 4L6 1Z" fill="currentColor" />
    </svg>
  ),
  history: (
    <svg width="16" height="16" viewBox="0 0 16 16" fill="none">
      <path d="M2 4H14M2 8H14M2 12H10" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" />
    </svg>
  ),
  profile: (
    <svg width="16" height="16" viewBox="0 0 16 16" fill="none">
      <circle cx="8" cy="6" r="2.5" stroke="currentColor" strokeWidth="1.3" />
      <path d="M3 14C3 11 5 9 8 9C11 9 13 11 13 14"
        stroke="currentColor" strokeWidth="1.3" strokeLinecap="round" />
    </svg>
  ),
  settings: (
    <svg width="16" height="16" viewBox="0 0 16 16" fill="none">
      <circle cx="8" cy="8" r="2" stroke="currentColor" strokeWidth="1.3" />
      <path d="M8 1V3M8 13V15M1 8H3M13 8H15"
        stroke="currentColor" strokeWidth="1.3" strokeLinecap="round" />
    </svg>
  ),
};

// V3.8 默认 16 入口菜单配置（5 分组 + Admin）
export const DEFAULT_SIDEBAR_GROUPS: SidebarMenuGroup[] = [
  {
    title: '概览',
    items: [
      { page: '/dashboard', href: '/dashboard', label: '今日概览', icon: ICON.dashboard },
    ],
  },
  {
    title: '面试',
    items: [
      { page: '/interview/profile', href: '/interview/profile', label: '今日面试', icon: ICON.interview, badge: 'new' },
      { page: '/interview/history', href: '/interview/history', label: '历史报告', icon: ICON.interview },
      { page: '/interview/setup', href: '/interview/setup', label: '面试配置', icon: ICON.settings },
    ],
  },
  {
    title: '学习复习',
    items: [
      { page: '/learn', href: '/learn', label: '题目浏览', icon: ICON.learn },
      { page: '/review', href: '/review', label: '复习中心', icon: ICON.learn },
      { page: '/plan', href: '/plan', label: '学习计划', icon: ICON.plan, badge: 'v3' },
      { page: '/collections', href: '/collections', label: '精选题单', icon: ICON.collections, badge: 'v3' },
    ],
  },
  {
    title: '知识库',
    items: [
      { page: '/knowledge', href: '/knowledge', label: '笔记浏览', icon: ICON.knowledge },
      { page: '/qa', href: '/qa', label: '问答社区', icon: ICON.qa },
      { page: '/report', href: '/report', label: '报告中心', icon: ICON.report },
    ],
  },
  {
    title: 'AI 推送',
    items: [
      { page: '/ai/today', href: '/ai/today', label: '今日推荐', icon: ICON.ai, badge: 'v3' },
      { page: '/ai/history', href: '/ai/history', label: '推送历史', icon: ICON.history },
    ],
  },
  {
    title: '我的',
    items: [
      { page: '/profile', href: '/profile', label: '我的画像', icon: ICON.profile },
      { page: '/settings', href: '/settings', label: '设置', icon: ICON.settings },
    ],
  },
  {
    title: 'ADMIN',
    titleColor: '#f59e0b',
    items: [
      { page: '/admin/questions', href: '/admin/questions', label: '题库管理', icon: ICON.settings, badge: 'admin' },
      { page: '/admin/sync', href: '/admin/sync', label: '手动同步', icon: ICON.ai, badge: 'admin' },
    ],
  },
];

// breadcrumb 映射
const BREADCRUMB_MAP: Record<string, string> = {
  '/dashboard': '今日概览',
  '/interview/profile': '今日面试',
  '/interview/history': '历史报告',
  '/interview/setup': '面试配置',
  '/learn': '题目浏览',
  '/review': '复习中心',
  '/plan': '学习计划',
  '/collections': '精选题单',
  '/knowledge': '笔记浏览',
  '/qa': '问答社区',
  '/report': '报告中心',
  '/ai/today': '今日推荐',
  '/ai/history': '推送历史',
  '/profile': '我的画像',
  '/settings': '设置',
  '/admin/questions': '题库管理',
  '/admin/sync': '手动同步',
};

export interface LayoutProps {
  /** 当前 page 路径（用于 Sidebar active 判定 + breadcrumb）*/
  currentPage?: string;
  /** Sidebar 自定义菜单 */
  sidebarGroups?: SidebarMenuGroup[];
  /** localStorage 折叠 key */
  storageKey?: string;
  /** 用户名（TopNav 显示）*/
  userName?: string;
  /** 退出回调 */
  onLogout?: () => void;
  children: React.ReactNode;
}

export function Layout({
  currentPage = '/dashboard',
  sidebarGroups = DEFAULT_SIDEBAR_GROUPS,
  storageKey = 'knockwise-sidebar-collapsed',
  userName,
  onLogout,
  children,
}: LayoutProps) {
  // 折叠状态提升到 Layout · Sidebar 受控 + main marginLeft 跟随
  const [collapsed, setCollapsed] = useState(false);

  // 启动时从 localStorage 读（SSR 后 hydrate）
  useEffect(() => {
    if (typeof window === 'undefined') return;
    try {
      const saved = localStorage.getItem(storageKey)
        ?? localStorage.getItem('intervue-sidebar-collapsed');
      if (saved === 'true' && !collapsed) {
        setCollapsed(true);
      }
    } catch { /* noop */ }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  // 同步 body class（用于其他可能的 CSS 选择器）
  useEffect(() => {
    if (typeof document !== 'undefined') {
      document.body.classList.toggle('sidebar-collapsed', collapsed);
    }
  }, [collapsed]);

  return (
    <div className="min-h-screen bg-[#050914] text-[#f1f5f9]">
      <TopNav
        breadcrumb={BREADCRUMB_MAP[currentPage] ?? ''}
        userName={userName ?? '开发者'}
        onLogout={onLogout}
      />

      <Sidebar
        groups={sidebarGroups}
        currentPage={currentPage}
        storageKey={storageKey}
        collapsed={collapsed}
        onCollapsedChange={setCollapsed}
      />

      <main
        role="main"
        style={{
          marginLeft: collapsed ? 64 : 240,
          padding: 24,
          minHeight: 'calc(100vh - 56px)',
          transition: 'margin-left 0.3s cubic-bezier(0.16, 1, 0.3, 1)',
        }}
      >
        {children}
      </main>
    </div>
  );
}

export default Layout;