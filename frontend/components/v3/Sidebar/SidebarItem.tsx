/**
 * SidebarItem — 单个菜单项（含 badge + active + icon）
 */
import React from 'react';
import { useRouter } from 'next/router';

export type SidebarItemBadge =
  | 'new'
  | 'v3'
  | 'admin'
  | { text: string; color?: string };

export interface SidebarItemProps {
  page?: string;
  active?: boolean;
  href?: string;
  onClick?: () => void;
  icon?: React.ReactNode;
  badge?: SidebarItemBadge;
  collapsed?: boolean;
  children: React.ReactNode;
  "data-testid"?: string;
  "data-page"?: string;
}

function renderBadge(badge: SidebarItemBadge | undefined) {
  if (!badge) return null;

  if (typeof badge === 'string') {
    if (badge === 'new') {
      return <span className="sidebar-badge">新</span>;
    }
    if (badge === 'v3') {
      return <span className="sidebar-badge">V3</span>;
    }
    if (badge === 'admin') {
      return <span className="tag-admin ml-auto text-[10px] px-1.5 py-0.5 rounded bg-amber-500/20 text-amber-300">🆕</span>;
    }
  }

  // 自定义 badge
  const custom = badge as { text: string; color?: string };
  return (
    <span
      className="sidebar-badge"
      style={custom.color ? { color: custom.color, borderColor: custom.color } : undefined}
    >
      {custom.text}
    </span>
  );
}

export function SidebarItem({
  page,
  active: activeProp,
  href,
  onClick,
  icon,
  badge,
  collapsed = false,
  children,
  'data-testid': testId,
  'data-page': dataPageAttr,
}: SidebarItemProps) {
  const router = useRouter();

  // active 判定：受控 prop 优先；否则用 router.pathname 或 data-page 比较
  const computedActive = activeProp ?? (
    page ? router.pathname.includes(page) : false
  );

  const handleClick = (e: React.MouseEvent) => {
    e.preventDefault();
    if (onClick) {
      onClick();
      return;
    }
    if (href) {
      router.push(href);
      return;
    }
    if (page) {
      router.push(`/${page}`);
    }
  };

  return (
    <button
      type="button"
      data-testid={testId}
      data-page={dataPageAttr ?? page}
      className={`sidebar-item ${computedActive ? 'active' : ''}`}
      onClick={handleClick}
      style={{
        display: 'flex',
        alignItems: 'center',
        gap: 10,
        width: '100%',
        padding: collapsed ? '10px' : '8px 10px',
        justifyContent: collapsed ? 'center' : 'flex-start',
        background: computedActive ? 'rgba(99, 102, 241, 0.12)' : 'transparent',
        border: 'none',
        borderRadius: 8,
        color: computedActive ? 'white' : '#94a3b8',
        fontSize: 13,
        fontWeight: 500,
        cursor: 'pointer',
        textAlign: 'left',
        fontFamily: 'inherit',
        position: 'relative',
        boxShadow: computedActive ? 'inset 2px 0 0 #6366f1' : 'none',
        transition: 'all 0.15s cubic-bezier(0.16, 1, 0.3, 1)',
      }}
    >
      {icon}
      {!collapsed && <span>{children}</span>}
      {!collapsed && renderBadge(badge)}
    </button>
  );
}

export default SidebarItem;