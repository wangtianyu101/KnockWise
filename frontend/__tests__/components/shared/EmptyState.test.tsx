/**
 * EmptyState 共享组件测试（V1 closure 🟡 #4）
 */
import { describe, it, expect, vi } from 'vitest';
import { render, screen } from '@testing-library/react';

import EmptyState from '@/components/shared/EmptyState';

describe('<EmptyState />', () => {
  it('渲染标题', () => {
    render(<EmptyState type="knowledge" title="暂无笔记" />);
    expect(screen.getByText('暂无笔记')).toBeInTheDocument();
  });

  it('渲染描述（可选）', () => {
    render(
      <EmptyState
        type="knowledge"
        title="答 3 道题后"
        description="答完第一道题后才会生成沉淀笔记"
      />
    );
    expect(
      screen.getByText('答完第一道题后才会生成沉淀笔记'),
    ).toBeInTheDocument();
  });

  it('4 种 type 各自渲染对应 SVG', () => {
    const { rerender } = render(<EmptyState type="knowledge" title="t" />);
    expect(screen.getByTestId('empty-icon-knowledge')).toBeInTheDocument();

    rerender(<EmptyState type="progress" title="t" />);
    expect(screen.getByTestId('empty-icon-progress')).toBeInTheDocument();

    rerender(<EmptyState type="data" title="t" />);
    expect(screen.getByTestId('empty-icon-data')).toBeInTheDocument();

    rerender(<EmptyState type="vault" title="t" />);
    expect(screen.getByTestId('empty-icon-vault')).toBeInTheDocument();
  });

  it('CTA 按钮（可选）点击触发 onCta', () => {
    const onClick = vi.fn();
    render(
      <EmptyState
        type="progress"
        title="今天没学习"
        ctaText="开始学习"
        onCta={onClick}
      />
    );
    const btn = screen.getByText('开始学习');
    btn.click();
    expect(onClick).toHaveBeenCalledTimes(1);
  });

  it('无 ctaText 时不渲染按钮', () => {
    render(<EmptyState type="vault" title="Obsidian 路径不存在" />);
    // 没有 ctaText → 不应该有按钮
    expect(screen.queryByRole('button')).toBeNull();
  });
});
