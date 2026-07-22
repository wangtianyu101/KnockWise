/**
 * SidebarSearch — 搜索框 + 实时过滤
 */
import React, { useState } from 'react';

export interface SidebarSearchProps {
  placeholder?: string;
  onSearch: (query: string) => void;
  defaultValue?: string;
  "data-testid"?: string;
}

export function SidebarSearch({
  placeholder = '搜索页面...',
  onSearch,
  defaultValue = '',
  'data-testid': testId = 'sidebar-search',
}: SidebarSearchProps) {
  const [value, setValue] = useState(defaultValue);

  return (
    <div className="sidebar-search" data-testid={testId}>
      <svg width="14" height="14" viewBox="0 0 14 14" fill="none">
        <circle cx="6" cy="6" r="4" stroke="currentColor" strokeWidth="1.5" />
        <path d="M9 9L12 12" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" />
      </svg>
      <input
        type="text"
        value={value}
        onChange={(e) => {
          setValue(e.target.value);
          onSearch(e.target.value);
        }}
        placeholder={placeholder}
      />
    </div>
  );
}

export default SidebarSearch;