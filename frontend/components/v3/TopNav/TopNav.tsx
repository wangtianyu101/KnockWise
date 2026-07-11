/**
 * TopNav — V3.8 P1 极简顶部 nav
 *
 * 结构（mockup L700-729）：
 * - 左：KnockWise logo + brand
 * - 中：breadcrumb（当前 page 名）
 * - 右：日期 + 用户头像 + 用户名
 *
 * V3.8 重构后：不再有 7 tab 横条（全部移到 Sidebar）
 */
import React from 'react';

const LOGO = (
  <svg width="28" height="28" viewBox="0 0 28 28" fill="none">
    <defs>
      <linearGradient id="logo-grad-topnav" x1="0" y1="0" x2="28" y2="28">
        <stop stopColor="#6366f1" />
        <stop offset="1" stopColor="#a78bfa" />
      </linearGradient>
    </defs>
    <rect x="2" y="2" width="24" height="24" rx="7" fill="url(#logo-grad-topnav)" />
    <path d="M10 8L10 20M10 20L13 17M10 20L13 23"
      stroke="white" strokeWidth="2" strokeLinecap="round" />
    <path d="M17 11L17 17M17 17L20 14M17 17L20 20"
      stroke="white" strokeWidth="2" strokeLinecap="round" opacity="0.5" />
  </svg>
);

export interface TopNavProps {
  /** 当前 page 名（breadcrumb 显示）*/
  breadcrumb?: string;
  /** 用户名 */
  userName?: string;
  /** 用户头像 URL（可选，不传则用渐变首字母）*/
  userAvatar?: string;
  /** 退出回调 */
  onLogout?: () => void;
  /** 日期（可选，默认今天）*/
  date?: string;
  "data-testid"?: string;
}

export function TopNav({
  breadcrumb = '',
  userName = '用户',
  userAvatar,
  onLogout,
  date,
  'data-testid': testId = 'topnav',
}: TopNavProps) {
  const today = date ?? new Date().toISOString().slice(0, 10);

  return (
    <nav
      data-testid={testId}
      className="sticky top-0 z-50 flex items-center gap-1 px-6 py-3.5 bg-[rgba(5,9,20,0.85)] backdrop-blur-xl border-b border-white/5"
    >
      {/* 左：Logo + brand */}
      <div className="flex items-center gap-3">
        {LOGO}
        <span className="font-bold text-lg">KnockWise</span>
      </div>

      {/* 中：breadcrumb */}
      {breadcrumb && (
        <span className="text-base font-semibold text-white ml-6">
          {breadcrumb}
        </span>
      )}

      {/* 右：日期 + 用户 */}
      <div className="ml-auto flex items-center gap-4">
        <span className="text-xs text-gray-500 hidden sm:inline">📅 {today}</span>
        <button
          type="button"
          onClick={onLogout}
          className="flex items-center gap-2 hover:opacity-80 transition-opacity"
          aria-label="用户菜单"
        >
          {userAvatar ? (
            <img src={userAvatar} alt={userName} className="w-7 h-7 rounded-full" />
          ) : (
            <div
              className="w-7 h-7 rounded-full flex items-center justify-center text-sm font-bold text-white"
              style={{ background: 'linear-gradient(135deg, #6366f1, #ec4899)' }}
            >
              {userName[0]?.toUpperCase() ?? '?'}
            </div>
          )}
          <span className="text-sm text-gray-200 hidden sm:inline">{userName}</span>
        </button>
      </div>
    </nav>
  );
}

export default TopNav;