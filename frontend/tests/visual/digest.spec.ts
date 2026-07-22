/**
 * Visual regression tests for digest UI (T28 · 决策 1 § 4)
 *
 * 与 frontend/tests/e2e/digest.spec.ts（功能 e2e）配合：
 * - e2e/digest.spec.ts: 验证 5 个用户场景的行为（点击/导航/状态变更）
 * - visual/digest.spec.ts（本文件）: 验证渲染外观与 baseline 一致
 *
 * 用法：
 *   npx playwright test visual/digest.spec.ts                    # 跑视觉对比
 *   npx playwright test visual/digest.spec.ts --update-snapshots  # 视觉改动后更新 baseline
 *
 * baseline 截图存 frontend/tests/visual/digest.spec.ts-snapshots/
 *
 * 注意：dev server (3000) + backend (8000) 必须先启动（playwright.config.ts webServer 段会自动起）
 */

import { test, expect } from '@playwright/test';

test.describe('AI 推送 视觉回归', () => {
  test.beforeEach(async ({ page }) => {
    // dev-login 拿 token（与 e2e 同步）
    await page.goto('/login');
    const token = await page.evaluate(async () => {
      const res = await fetch('/api/auth/dev-login?user_id=1');
      const data = await res.json();
      return data.access_token;
    });
    await page.evaluate((t) => localStorage.setItem('token', t), token);
  });

  test('页面 /ai/today 渲染', async ({ page }) => {
    await page.goto('/ai/today');
    await page.waitForLoadState('networkidle');
    await expect(page).toHaveScreenshot('digest-today.png', { maxDiffPixels: 100 });
  });

  test('页面 /ai/bookmarks 渲染', async ({ page }) => {
    await page.goto('/ai/bookmarks');
    await page.waitForLoadState('networkidle');
    await expect(page).toHaveScreenshot('digest-bookmarks.png', { maxDiffPixels: 100 });
  });

  test('页面 /ai/settings 渲染', async ({ page }) => {
    await page.goto('/ai/settings');
    await page.waitForLoadState('networkidle');
    await expect(page).toHaveScreenshot('digest-settings.png', { maxDiffPixels: 100 });
  });
});
