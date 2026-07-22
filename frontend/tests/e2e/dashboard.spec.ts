/**
 * V3.8 P5 · Dashboard 视觉回归测试
 *
 * 覆盖：Dashboard 6 组件（HeroCard + StatsBar + RadarMini + 3 核心卡 + 5 入口）
 * 实际生产数据来自 dev-login (user_id=e9659aa7-37cd-4e3e-b52b-4f51996f2760)
 */
import { test, expect } from '@playwright/test';

test.describe('Dashboard V3.8 视觉回归', () => {
  test.beforeEach(async ({ page }) => {
    // 走 dev-login 拿 token（V3.8 dev 环境）
    const resp = await page.request.get('http://localhost:8000/api/auth/dev-login');
    const data = await resp.json();
    // 设 token 到 localStorage
    await page.addInitScript((t) => {
      window.localStorage.setItem('knockwise_token', t);
    }, data.access_token);
    // 等 Layout 加载完成
    await page.goto('/dashboard');
    await page.waitForSelector('[data-testid="sidebar"]');
  });

  test('dashboard 完整页面截图', async ({ page }) => {
    await page.goto('/dashboard');
    await page.waitForLoadState('networkidle');
    // 等 HeroCard 出现
    await page.waitForSelector('[data-testid="hero-card"]', { timeout: 5000 });
    // 等 skeleton → 真实内容
    await page.waitForTimeout(1500); // 给 API 调用 + 渲染完成时间
    await expect(page).toHaveScreenshot('dashboard-full.png', { fullPage: true });
  });

  test('HeroCard 渲染', async ({ page }) => {
    await page.goto('/dashboard');
    await page.waitForSelector('[data-testid="hero-card"]');
    await page.waitForTimeout(1500);
    await expect(page.locator('[data-testid="hero-card"]')).toHaveScreenshot('dashboard-herocard.png');
  });

  test('StatsBar 5 列渲染', async ({ page }) => {
    await page.goto('/dashboard');
    await page.waitForSelector('[data-testid="stats-bar"]');
    await expect(page.locator('[data-testid="stats-bar"]')).toHaveScreenshot('dashboard-statsbar.png');
  });

  test('Sidebar 展开态（240px）', async ({ page }) => {
    await page.goto('/dashboard');
    await page.waitForSelector('[data-testid="sidebar"]:not(.collapsed)');
    await expect(page.locator('[data-testid="sidebar"]')).toHaveScreenshot('sidebar-expanded.png');
  });

  test('Sidebar 折叠态（64px）', async ({ page }) => {
    await page.goto('/dashboard');
    await page.waitForSelector('[data-testid="sidebar"]');
    await page.click('button[aria-label*="折叠侧栏"]');
    await page.waitForTimeout(500); // 等过渡动画
    await expect(page.locator('[data-testid="sidebar"]')).toHaveScreenshot('sidebar-collapsed.png');
  });

  test('TopNav 极简版', async ({ page }) => {
    await page.goto('/dashboard');
    await page.waitForSelector('[data-testid="topnav"]');
    await expect(page.locator('[data-testid="topnav"]')).toHaveScreenshot('dashboard-topnav.png');
  });
});