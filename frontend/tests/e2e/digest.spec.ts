import { expect, test, type Page, type Route } from '@playwright/test';

const digestItems = Array.from({ length: 5 }, (_, index) => ({
  id: `item-${index + 1}`,
  rank: index + 1,
  title: `Digest fixture ${index + 1}`,
  summary: `Deterministic summary ${index + 1}`,
  quality_score: 0.95 - index * 0.02,
  type: index % 2 === 0 ? 'model' : 'application',
  region: index % 2 === 0 ? 'overseas' : 'domestic',
  category: 'headline',
  source_name: 'Harness Fixture',
  source_url: `https://example.com/${index + 1}`,
  published_at: '2026-07-22T00:00:00Z',
  estimated_minutes: 3,
  is_read: false,
  is_bookmarked: false,
  related_item_ids: [],
}));

async function fulfillJson(route: Route, body: unknown, status = 200) {
  await route.fulfill({
    status,
    contentType: 'application/json',
    body: JSON.stringify(body),
  });
}

async function installDigestApi(page: Page) {
  let settings = {
    user_id: 'user-e2e',
    push_hour: 8,
    push_minute: 0,
    push_timezone: 'Asia/Shanghai',
    email_enabled: true,
    interested_tags: ['AI'],
    blocked_tags: [],
  };

  await page.route('**/api/digest/**', async (route) => {
    const request = route.request();
    const pathname = new URL(request.url()).pathname;

    if (pathname === '/api/digest/today') {
      return fulfillJson(route, {
        date: '2026-07-22',
        vibe: '今日 5 条 · 正常推送',
        item_count: 5,
        items: digestItems,
      });
    }
    if (pathname === '/api/digest/bookmarks' && request.method() === 'GET') {
      return fulfillJson(route, {
        total: 1,
        items: [{ ...digestItems[0], item_id: digestItems[0].id }],
      });
    }
    if (pathname === '/api/digest/bookmarks' && request.method() === 'POST') {
      return fulfillJson(route, { id: 'bookmark-1' }, 201);
    }
    if (pathname === '/api/digest/hide' && request.method() === 'POST') {
      return fulfillJson(route, { hide_id: 'hide-1' });
    }
    if (pathname === '/api/digest/settings' && request.method() === 'PATCH') {
      settings = { ...settings, ...(request.postDataJSON() as object) };
      return fulfillJson(route, settings);
    }
    if (pathname === '/api/digest/settings') {
      return fulfillJson(route, settings);
    }
    return fulfillJson(route, { detail: `Unhandled fixture route: ${pathname}` }, 404);
  });
}

test.describe('AI 推送端到端', () => {
  test.beforeEach(async ({ page }) => {
    await page.addInitScript(() => localStorage.setItem('knockwise_token', 'playwright-e2e'));
    await installDigestApi(page);
  });

  test('场景 1: 打开 /ai/today 看到 5 条 digest', async ({ page }) => {
    await page.goto('/ai/today');
    await expect(page.locator('.digest-card')).toHaveCount(5);
    await expect(page.locator('.vibe-badge')).toContainText('今日 5 条');
  });

  test('场景 2: 收藏后卡片显示已收藏', async ({ page }) => {
    await page.goto('/ai/today');
    const firstCard = page.locator('.digest-card').first();
    await firstCard.getByTitle('收藏').click();
    await expect(firstCard.getByTitle('已收藏')).toBeVisible();
  });

  test('场景 3: 屏蔽操作打开 HideDialog', async ({ page }) => {
    await page.goto('/ai/today');
    await page.locator('.digest-card').first().getByTitle('屏蔽').click();
    await expect(page.locator('.modal-content')).toBeVisible();
    await expect(page.getByText('不再推送类似内容？')).toBeVisible();
  });

  test('场景 4: /ai/bookmarks 显示收藏数据', async ({ page }) => {
    await page.goto('/ai/bookmarks');
    await expect(page.getByRole('heading', { name: /我的收藏/ })).toBeVisible();
    await expect(page.getByText('Digest fixture 1')).toBeVisible();
  });

  test('场景 5: /ai/settings 保存推送时间', async ({ page }) => {
    await page.goto('/ai/settings');
    await page.locator('input[type="number"]').first().fill('7');
    await page.getByRole('button', { name: '保存设置' }).click();

    await expect.poll(async () => page.evaluate(async () => {
      const response = await fetch('/api/digest/settings');
      const data = await response.json();
      return data.push_hour;
    })).toBe(7);
  });
});
