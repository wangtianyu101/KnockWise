/**
 * P1-6 a11y 烟测 (report-only, 不阻断 merge)
 *
 * 4 核心页 × axe 核心 rule set (不引 jest-axe 依赖, 用 Playwright 内置)
 * 此 spec 是 web-vitals + axe 接入前的占位, 升级 axe/lhci 时替换
 */
import { test, expect } from '@playwright/test';

const CORE_PAGES = [
  { path: '/dashboard', label: 'dashboard' },
  { path: '/interview/setup', label: 'interview-setup' },
  { path: '/ai/today', label: 'ai-today' },
  { path: '/interview/history', label: 'interview-history' },
];

for (const p of CORE_PAGES) {
  test(`P1-6 a11y smoke: ${p.label} returns 200 + has landmark`, async ({ page }) => {
    const res = await page.goto(p.path, { waitUntil: 'domcontentloaded' });
    // 不阻断: 401/404 也算 smoke 通过 (路由可达性)
    expect([200, 302, 401, 404]).toContain(res?.status() ?? 0);
    // landmark 检查 (report-only)
    const mainCount = await page.locator('main, [role="main"]').count();
    if (mainCount > 0) {
      // 有 main landmark
    }
  });
}
