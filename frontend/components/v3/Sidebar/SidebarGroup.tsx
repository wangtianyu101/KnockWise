/**
 * SidebarGroup — 分组标题 + 子内容容器
 */
import React from 'react';

export interface SidebarGroupProps {
  title: string;
  icon?: React.ReactNode;
  titleColor?: string;
  children: React.ReactNode;
  defaultCollapsed?: boolean;
  collapsed?: boolean;
  onCollapsedChange?: (collapsed: boolean) => void;
  "data-testid"?: string;
}

export function SidebarGroup({
  title,
  icon,
  titleColor,
  children,
  defaultCollapsed = false,
  collapsed: collapsedProp,
  onCollapsedChange,
  'data-testid': testId = 'sidebar-group',
}: SidebarGroupProps) {
  const [internalCollapsed, setInternalCollapsed] = React.useState(defaultCollapsed);
  const isControlled = collapsedProp !== undefined;
  const collapsed = isControlled ? collapsedProp : internalCollapsed;

  const toggle = () => {
    const next = !collapsed;
    if (isControlled) onCollapsedChange?.(next);
    else setInternalCollapsed(next);
  };

  return (
    <div className="sidebar-group-content" data-testid={testId}>
      <div
        className="sidebar-group-title"
        data-testid={`${testId}-title`}
        style={titleColor ? { color: titleColor } : undefined}
        onClick={toggle}
        role="button"
      >
        {icon}
        <span>{title}</span>
      </div>
      <div
        className={`sidebar-group-children ${collapsed ? 'hidden' : ''}`}
      >
        {children}
      </div>
    </div>
  );
}

export default SidebarGroup;