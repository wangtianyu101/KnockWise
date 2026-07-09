/**
 * StatCard 共享组件测试
 */
import { describe, it, expect, vi } from 'vitest';
import { render, screen } from '@testing-library/react';

vi.mock('next/router', () => ({ useRouter: () => ({ push: vi.fn() }) }));

import StatCard from '@/components/shared/StatCard';

describe('<StatCard />', () => {
  it('渲染 label 和 value', () => {
    render(<StatCard label="已做" value={18} />);
    expect(screen.getByText('已做')).toBeInTheDocument();
    expect(screen.getByText('18')).toBeInTheDocument();
  });

  it('渲染 suffix', () => {
    render(<StatCard label="笔记" value={3} suffix="篇" />);
    expect(screen.getByText('篇')).toBeInTheDocument();
    expect(screen.getByText('3')).toBeInTheDocument();
  });

  it('字符串 value', () => {
    render(<StatCard label="连续" value="12天" />);
    expect(screen.getByText('12天')).toBeInTheDocument();
  });

  it('颜色映射到不同 text-color', () => {
    const { rerender, container } = render(
      <StatCard label="已做" value={1} color="indigo" />
    );
    expect(container.innerHTML).toMatch(/color:\s*#a5b4fc/);

    rerender(<StatCard label="已掌握" value={1} color="emerald" />);
    expect(container.innerHTML).toMatch(/color:\s*#34d399/);

    rerender(<StatCard label="学习中" value={1} color="blue" />);
    expect(container.innerHTML).toMatch(/color:\s*#60a5fa/);

    rerender(<StatCard label="连续" value={1} color="amber" />);
    expect(container.innerHTML).toMatch(/color:\s*#fbbf24/);
  });

  it('size=md 字号比 sm 大', () => {
    const { rerender, container: c1 } = render(
      <StatCard label="x" value={1} size="sm" />
    );
    const { container: c2 } = render(
      <StatCard label="x" value={1} size="md" />
    );
    // sm 24px, md 36px（CSS 内联样式，冒号后可能有空格）
    expect(c1.innerHTML).toMatch(/font-size:\s*24px/);
    expect(c2.innerHTML).toMatch(/font-size:\s*36px/);
  });
});
