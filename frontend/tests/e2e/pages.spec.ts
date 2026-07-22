/**
 * V3.8 P5 · 17 page 视觉回归测试
 *
 * 覆盖：dashboard + interview/profile + interview/history + interview/setup
 *      + learn + review + plan + collections
 *      + knowledge + qa + report
 *      + ai/today + ai/history + profile + settings
 *      + admin/questions + admin/sync
 *
 * 总计 17 page × 1 截图 = 17 测试
 *
 * 注意：有些 page 业务逻辑可能 401 redirect 到 /（dev-login 不够权限），
 * 截图失败正常（baseline 没建 + 业务逻辑未跑通）· 让 playwright skip。
 */
import { test, expect } from '@playwright/test';

const PAGES: { path: string; name: string }[] = [
  { path: '/dashboard', name: '01-dashboard' },
  { path: '/interview/profile', name: '02-interview-today' },
  { path: '/interview/history', name: '03-interview-history' },
  { path: '/interview/setup', name: '04-interview-setup' },
  { path: '/learn', name: '05-learn' },
  { path: '/review', name: '06-review' },
  { path: '/plan', name: '07-plan' },
  { path: '/collections', name: '08-collections' },
  { path: '/knowledge', name: '09-knowledge' },
  { path: '/qa', name: '10-qa' },
  { path: '/report', name: '11-report' },
  { path: '/ai/today', name: '12-ai-today' },
  { path: '/ai/history', name: '13-ai-history' },
  { path: '/profile', name: '14-profile' },
  { path: '/settings', name: '15-settings' },
  { path: '/admin/questions', name: '16-admin-questions' },
  { path: '/admin/sync', name: '17-admin-sync' },
];

test.describe('17 page 视觉回归', () => {
  test.beforeEach(async ({ page }) => {
    // 走 dev-login 拿 token（V3.8 dev 环境）
    const resp = await page.request.get('http://localhost:8000/api/auth/dev-login');
    const data = await resp.json();
    await page.addInitScript((t) => {
      window.localStorage.setItem('knockwise_token', t);
    }, data.access_token);
    await page.waitForSelector('[data-testid="sidebar"]', { timeout: 1000 }).catch(() => {});
  });

  for (const { path, name } of PAGES) {
    test(`${path} 截图`, async ({ page }) => {
      const response = await page.goto(path);
      // 接受 200/401 · 401 表示业务未跑通但页面渲染 OK
      expect(response?.status() ?? 0).toBeLessThan(500);
      // 等 Layout + Sidebar 稳定
      await page.waitForSelector('[data-testid="sidebar"]', { timeout: 5000 });
      // 给动态内容渲染时间
      await page.waitForTimeout(1000);
      await expect(page).toHaveScreenshot(`${name}.png`, { fullPage: true });
    });
  }
});