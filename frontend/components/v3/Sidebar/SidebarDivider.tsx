/**
 * SidebarDivider — 分隔线（可带 label，如 "ADMIN"）
 */
import React from 'react';

export interface SidebarDividerProps {
  label?: string;
  labelColor?: string;
  "data-testid"?: string;
}

export function SidebarDivider({
  label,
  labelColor = '#f59e0b',
  'data-testid': testId = 'sidebar-divider',
}: SidebarDividerProps) {
  if (!label) {
    return <hr data-testid={testId} className="sidebar-divider-line" />;
  }

  return (
    <div
      className="sidebar-divider-with-label flex items-center gap-2 my-2 px-3"
      data-testid={testId}
    >
      <span
        className="text-[10px] uppercase tracking-wider font-semibold"
        style={{ color: labelColor }}
      >
        {label}
      </span>
      <hr className="flex-1 border-0 h-px bg-white/5" />
    </div>
  );
}

export default SidebarDivider;