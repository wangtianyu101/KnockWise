/**
 * SidebarHeader — 顶部 logo + 品牌名 + 折叠按钮
 */
import React from 'react';
import Link from 'next/link';

// KnockWise 默认 logo SVG（候选 A：敲门图标）
const DEFAULT_LOGO = (
  <svg width="22" height="22" viewBox="0 0 28 28" fill="none">
    <defs>
      <linearGradient id="logo-grad-header" x1="0" y1="0" x2="28" y2="28">
        <stop stopColor="#6366f1" />
        <stop offset="1" stopColor="#a78bfa" />
      </linearGradient>
    </defs>
    <rect x="2" y="2" width="24" height="24" rx="7" fill="url(#logo-grad-header)" />
    <path d="M10 8L10 20M10 20L13 17M10 20L13 23"
      stroke="white" strokeWidth="2" strokeLinecap="round" />
    <path d="M17 11L17 17M17 17L20 14M17 17L20 20"
      stroke="white" strokeWidth="2" strokeLinecap="round" opacity="0.5" />
  </svg>
);

export interface SidebarHeaderProps {
  brand?: string;
  logo?: React.ReactNode;
  collapsed: boolean;
  onToggle: () => void;
  "data-testid"?: string;
}

export function SidebarHeader({
  brand = 'KnockWise',
  logo = DEFAULT_LOGO,
  collapsed,
  onToggle,
  'data-testid': testId = 'sidebar-header',
}: SidebarHeaderProps) {
  return (
    <div className="sidebar-header" data-testid={testId}>
      <Link
        href="/dashboard"
        className="flex items-center gap-2"
        style={{ textDecoration: 'none' }}
      >
        {logo}
        <span className="sidebar-logo">{brand}</span>
      </Link>
      <button
        type="button"
        className="sidebar-toggle"
        onClick={onToggle}
        title={collapsed ? '展开' : '折叠'}
        aria-label={collapsed ? '展开侧栏' : '折叠侧栏'}
      >
        <svg width="16" height="16" viewBox="0 0 16 16" fill="none">
          {collapsed ? (
            <path d="M6 4L10 8L6 12" stroke="currentColor"
              strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round" />
          ) : (
            <path d="M10 4L6 8L10 12" stroke="currentColor"
              strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round" />
          )}
        </svg>
      </button>
    </div>
  );
}

export default SidebarHeader;