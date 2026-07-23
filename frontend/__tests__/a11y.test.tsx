/**
 * P1-6 a11y unit tests (不引 jest-axe, 用 @testing-library/jest-dom 已断言)
 */
import { describe, it, expect } from 'vitest';
import { render, screen } from '@testing-library/react';
import { StatCard } from '@/components/shared/StatCard';

describe('P1-6 a11y unit: StatCard', () => {
  it('has accessible label via aria-label or text', () => {
    render(<StatCard label="今日面试" value={5} />);
    expect(screen.getByText('今日面试')).toBeInTheDocument();
  });
  it('value visible (not hidden from screen readers)', () => {
    render(<StatCard label="完成率" value="80%" />);
    const value = screen.getByText('80%');
    expect(value).not.toHaveAttribute('aria-hidden', 'true');
  });
});
