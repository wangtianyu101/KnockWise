// tests/e2e/digest.spec.ts · T29 Playwright E2E
// 端到端测试 · 覆盖 5 个用户场景
import { test, expect } from '@playwright/test';

test.describe('AI 推送 端到端', () => {
  test.beforeEach(async ({ page }) => {
    await page.goto('/login');
    // dev-login 拿 token
    const token = await page.evaluate(async () => {
      const res = await fetch('/api/auth/dev-login?user_id=1');
      const data = await res.json();
      return data.access_token;
    });
    await page.evaluate((t) => localStorage.setItem('token', t), token);
  });

  test('场景 1: 打开 /ai/today 看到 5 条 digest', async ({ page }) => {
    await page.goto('/ai/today');
    await expect(page.locator('.digest-card')).toHaveCount(5);
    await expect(page.locator('.vibe-badge')).toBeVisible();
  });

  test('场景 2: 点 🔖 收藏 · 卡片变实心', async ({ page }) => {
    await page.goto('/ai/today');
    const firstCard = page.locator('.digest-card').first();
    await firstCard.locator('button[title="收藏"]').click();
    await expect(firstCard.locator('button[title="已收藏"]')).toBeVisible();
  });

  test('场景 3: 点 🔇 屏蔽 → 弹 HideDialog modal', async ({ page }) => {
    await page.goto('/ai/today');
    const firstCard = page.locator('.digest-card').first();
    await firstCard.locator('button[title="屏蔽"]').click();
    await expect(page.locator('.modal-content')).toBeVisible();
    await expect(page.locator('text=不再推送类似内容？')).toBeVisible();
  });

  test('场景 4: /ai/bookmarks 显示我的收藏', async ({ page }) => {
    await page.goto('/ai/bookmarks');
    await expect(page.locator('h1')).toContainText('我的收藏');
  });

  test('场景 5: /ai/settings 改推送时间 → 保存', async ({ page }) => {
    await page.goto('/ai/settings');
    const hourInput = page.locator('input[type="number"]').first();
    await hourInput.fill('7');
    await page.locator('button:has-text("保存设置")').click();
    // 验证后端：fetch settings → push_hour 应该是 7
    const newHour = await page.evaluate(async () => {
      const res = await fetch('/api/digest/settings');
      const data = await res.json();
      return data.push_hour;
    });
    expect(newHour).toBe(7);
  });
});
