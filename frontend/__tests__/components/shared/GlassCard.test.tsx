/**
 * GlassCard 共享组件测试
 */
import { describe, it, expect, vi } from 'vitest';
import { render, screen } from '@testing-library/react';

vi.mock('next/router', () => ({ useRouter: () => ({ push: vi.fn() }) }));

import GlassCard from '@/components/shared/GlassCard';

describe('<GlassCard />', () => {
  it('渲染 children', () => {
    render(<GlassCard>Hello card</GlassCard>);
    expect(screen.getByText('Hello card')).toBeInTheDocument();
  });

  it('默认 variant 应用玻璃卡 className', () => {
    const { container } = render(<GlassCard data-testid="c">x</GlassCard>);
    const el = container.querySelector('[data-testid="c"]')!;
    expect(el.className).toContain('bg-white/[0.03]');
    expect(el.className).toContain('backdrop-blur-xl');
    expect(el.className).toContain('border-indigo-500/10');
    expect(el.className).toContain('rounded-2xl');
  });

  it('hover-lift variant 加 hover 效果', () => {
    const { container } = render(
      <GlassCard data-testid="c" variant="hover-lift">x</GlassCard>
    );
    const el = container.querySelector('[data-testid="c"]')!;
    expect(el.className).toContain('cursor-pointer');
    expect(el.className).toContain('hover:border-indigo-500/30');
    expect(el.className).toContain('transition-all');
  });

  it('padding="sm" 应用 p-4，padding="md" 应用 p-7', () => {
    const { container: c1 } = render(
      <GlassCard data-testid="a" padding="sm">x</GlassCard>
    );
    const { container: c2 } = render(
      <GlassCard data-testid="b" padding="md">x</GlassCard>
    );
    expect(c1.querySelector('[data-testid="a"]')!.className).toContain('p-4');
    expect(c2.querySelector('[data-testid="b"]')!.className).toContain('p-7');
  });

  it('onClick 可触发点击', () => {
    const onClick = vi.fn();
    const { container } = render(
      <GlassCard onClick={onClick} data-testid="c">x</GlassCard>
    );
    container.querySelector('[data-testid="c"]')!.click();
    expect(onClick).toHaveBeenCalledTimes(1);
  });
});
