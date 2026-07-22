/**
 * Sidebar 容器组件 — V3.8 P1
 *
 * 状态管理：
 * - 折叠状态（受控或非受控 + localStorage 持久化）
 * - 移动端 drawer 开关（受控）
 *
 * 受控 vs 非受控：
 * - 传 `collapsed` + `onCollapsedChange` → 受控
 * - 不传 → 非受控，内部 useState + localStorage 持久化（key: knockwise-sidebar-collapsed）
 */
import React, { useState, useEffect, useCallback } from 'react';
import { useRouter } from 'next/router';
import { SidebarHeader } from './SidebarHeader';
import { SidebarSearch } from './SidebarSearch';
import { SidebarGroup } from './SidebarGroup';
import { SidebarItem } from './SidebarItem';
import { SidebarDivider } from './SidebarDivider';

// ── 类型导出 ─────────────────────────────────────────────────────────
export interface SidebarMenuItem {
  page: string;
  href?: string;
  onClick?: () => void;
  icon: React.ReactNode;
  label: string;
  badge?: 'new' | 'v3' | 'admin' | { text: string; color?: string };
}

export interface SidebarMenuGroup {
  title: string;
  icon?: React.ReactNode;
  titleColor?: string;
  items: SidebarMenuItem[];
  defaultCollapsed?: boolean;
}

export interface SidebarProps {
  currentPage?: string;
  collapsed?: boolean;
  onCollapsedChange?: (collapsed: boolean) => void;
  mobileOpen?: boolean;
  onMobileClose?: () => void;
  groups: SidebarMenuGroup[];
  storageKey?: string;
  onSearch?: (query: string) => void;
  "data-testid"?: string;
}

// ── localStorage 双 key fallback 工具 ───────────────────────────────
function loadCollapsed(storageKey: string): boolean {
  if (typeof window === 'undefined') return false;
  try {
    const v = localStorage.getItem(storageKey)
      ?? localStorage.getItem('intervue-sidebar-collapsed');
    return v === 'true';
  } catch { return false; }
}

function saveCollapsed(storageKey: string, collapsed: boolean) {
  if (typeof window === 'undefined') return;
  try {
    localStorage.setItem(storageKey, String(collapsed));
    localStorage.removeItem('intervue-sidebar-collapsed');
  } catch { /* noop */ }
}

// ── 组件 ─────────────────────────────────────────────────────────────
export function Sidebar({
  currentPage,
  collapsed: collapsedProp,
  onCollapsedChange,
  mobileOpen = false,
  onMobileClose,
  groups,
  storageKey = 'knockwise-sidebar-collapsed',
  onSearch,
  'data-testid': testId = 'sidebar',
}: SidebarProps) {
  const router = useRouter();

  // 受控 vs 非受控：未传 prop 则用内部 state + localStorage
  const [internalCollapsed, setInternalCollapsed] = useState(false);
  const isControlled = collapsedProp !== undefined;
  const collapsed = isControlled ? collapsedProp : internalCollapsed;

  // V3.8 P1 Bugfix: 搜索过滤（之前 onSearch 是空函数 · Layout 没传）
  const [searchQuery, setSearchQuery] = useState('');
  const handleSearch = useCallback((q: string) => {
    setSearchQuery(q);
    onSearch?.(q);
  }, [onSearch]);

  // SSR 阶段从 localStorage 读（避免 hydration mismatch）
  useEffect(() => {
    if (isControlled) return;
    const saved = loadCollapsed(storageKey);
    if (saved !== internalCollapsed) {
      setInternalCollapsed(saved);
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  const handleToggle = useCallback(() => {
    const next = !collapsed;
    if (isControlled) {
      onCollapsedChange?.(next);
    } else {
      setInternalCollapsed(next);
      saveCollapsed(storageKey, next);
    }
  }, [collapsed, isControlled, onCollapsedChange, storageKey]);

  // ESC 关闭 drawer
  useEffect(() => {
    if (!mobileOpen) return;
    const onKey = (e: KeyboardEvent) => {
      if (e.key === 'Escape') onMobileClose?.();
    };
    document.addEventListener('keydown', onKey);
    return () => document.removeEventListener('keydown', onKey);
  }, [mobileOpen, onMobileClose]);

  const handleItemClick = (item: SidebarMenuItem) => {
    if (item.onClick) {
      item.onClick();
    } else if (item.href) {
      router.push(item.href);
    } else {
      router.push(`/${item.page}`);
    }
  };

  // 渲染分组
  return (
    <aside
      data-testid={testId}
      className={[
        'sidebar',
        'flex flex-col',
        collapsed ? 'collapsed' : '',
        mobileOpen ? 'open' : '',
      ].filter(Boolean).join(' ')}
      style={{
        position: 'fixed',
        top: 56,
        left: 0,
        bottom: 0,
        width: collapsed ? 64 : 240,
        background: 'rgba(8, 12, 24, 0.85)',
        backdropFilter: 'blur(24px) saturate(180%)',
        WebkitBackdropFilter: 'blur(24px) saturate(180%)',
        borderRight: '1px solid rgba(148, 163, 184, 0.08)',
        padding: 16,
        zIndex: 50,
        transition: 'width 0.3s cubic-bezier(0.16, 1, 0.3, 1)',
      }}
    >
      <SidebarHeader
        brand="KnockWise"
        collapsed={collapsed}
        onToggle={handleToggle}
      />

      <SidebarSearch
        placeholder="搜索页面..."
        onSearch={handleSearch}
      />

      <nav className="sidebar-nav" data-testid="sidebar-nav">
        {groups
          // V3.8 P1: 搜索过滤 — 按 query 过滤 label/title
          .map((group) => ({
            ...group,
            items: searchQuery.trim()
              ? group.items.filter(
                  (it) =>
                    it.label.toLowerCase().includes(searchQuery.toLowerCase()) ||
                    group.title.toLowerCase().includes(searchQuery.toLowerCase())
                )
              : group.items,
          }))
          // 搜索时隐藏空分组
          .filter((group) => group.items.length > 0)
          .map((group, gi) => (
          <div key={gi} className="sidebar-group">
            <SidebarGroup
              title={group.title}
              icon={group.icon}
              titleColor={group.titleColor}
              defaultCollapsed={group.defaultCollapsed}
            >
              {group.items.map((item) => (
                <SidebarItem
                  key={item.page}
                  page={item.page}
                  href={item.href}
                  onClick={item.onClick ?? (() => handleItemClick(item))}
                  icon={item.icon}
                  badge={item.badge}
                  active={currentPage === item.page || currentPage === item.href}
                  collapsed={collapsed}
                  data-page={item.page}
                >
                  {item.label}
                </SidebarItem>
              ))}
            </SidebarGroup>
            {/* ADMIN 分组与上一组之间加分隔线 */}
            {gi < groups.length - 1 && group.title === 'ADMIN' && (
              <SidebarDivider />
            )}
          </div>
        ))}

        {/* Footer 状态 */}
        <div className="sidebar-footer">
          <div className="flex items-center justify-between">
            <span className="text-xs text-gray-500">V3.8 沉淀层</span>
            <span className="text-xs text-emerald-400">● 启用</span>
          </div>
        </div>
      </nav>
    </aside>
  );
}

export default Sidebar;