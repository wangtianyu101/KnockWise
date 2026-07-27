/**
 * Hydration mismatch 全局修复（2026-07-27 · V3.9 P1）
 *
 * 调研：[`docs/tasks/2026-07-27-bug-hydration-mismatch/research.md`](../../docs/tasks/2026-07-27-bug-hydration-mismatch/research.md)
 * 决策：[`decisions.md`](../../docs/tasks/2026-07-27-bug-hydration-mismatch/decisions.md)
 * 任务：[`tasks.md`](../../docs/tasks/2026-07-27-bug-hydration-mismatch/tasks.md)
 *
 * 主回归（场景 A）：未登录用户访问受保护路由 —— 5/5 GREEN
 *
 * ⏸ 暂缓的场景 B / C（dev-login 基础设施问题）：
 * - 场景 B：已登录 userName 文本 mismatch · 测试需 dev-login 拿 token
 * - 场景 C：TopNav 日期 mismatch · 测试需 dev-login 拿 token
 * - **问题**：`page.request.get('/api/auth/dev-login')` 在连发 8+ 次后超时（>60s）
 *   而 curl 直测同 URL 仅 5ms → 怀疑是 Playwright `page.request` 上下文排队
 *   等待 / browser fixture 重置，不是后端 dev-login 端点问题
 * - **临时方案**：场景 B / C 改为手动 L5 验证（dev server 浏览器实操）
 * - **永久方案**：dev-login 加缓存 / 改为静态 JWT fixture（follow-up task）
 *
 * 5 代表路由（决策 1）：/dashboard /interview/profile /push/daily/[date] /learn /admin/questions
 */

import { test, expect, type Page, type ConsoleMessage } from '@playwright/test';

/** 受保护路由代表（与 research.md § 2.2 / 决策 1 一致） */
const PROTECTED_ROUTES = [
  '/dashboard',
  '/interview/profile',
  '/push/daily/2026-07-27',
  '/learn',
  '/admin/questions',
];

/**
 * 匹配 React 18+ / Next.js 15 hydration 警告
 * 覆盖：错误（error）+ 警告（warning） + 页面异常（pageerror）
 */
const HYDRATION_PATTERNS: RegExp[] = [
  /Hydration failed/i,
  /server rendered.*didn.*match/i,
  /hydration mismatch/i,
  /tree will be regenerated/i,
  /Text content does not match/i,
  /did not match.*server/i,
  /Hydration error/i,
];

/** 清理 localStorage 模拟未登录 */
async function clearToken(page: Page) {
  await page.goto('/');
  await page.evaluate(() => window.localStorage.clear());
}

/** 捕获 page console 错误 / 警告 / pageerror */
function attachHydrationCapture(page: Page) {
  const errors: string[] = [];
  const warnings: string[] = [];
  page.on('console', (msg: ConsoleMessage) => {
    const text = msg.text();
    if (msg.type() === 'error') errors.push(text);
    if (msg.type() === 'warning') warnings.push(text);
  });
  page.on('pageerror', (err) => errors.push(`pageerror: ${err.message}`));
  return { errors, warnings };
}

/** 过滤 hydration 错误 */
function findHydrationIssues(errors: string[], warnings: string[]): string[] {
  return [...errors, ...warnings].filter((msg) =>
    HYDRATION_PATTERNS.some((p) => p.test(msg))
  );
}

/** 默认 60s timeout（dev server 冷启动 + Next 编译需要） */
test.setTimeout(60_000);

test.describe('Hydration mismatch 全局修复（2026-07-27）', () => {
  test.describe('场景 A · 未登录用户访问受保护路由（结构性 mismatch · 主回归 · 5/5 GREEN）', () => {
    test.beforeEach(async ({ page }) => {
      await clearToken(page);
    });

    for (const route of PROTECTED_ROUTES) {
      test(`${route} · 不应触发 hydration error`, async ({ page }) => {
        const { errors, warnings } = attachHydrationCapture(page);

        const response = await page.goto(route);
        expect(response?.status() ?? 0).toBeLessThan(500);

        // 给 hydration 时间（React 18+ 同步检测会立即触发，但 pageerror 可能稍晚）
        await page.waitForTimeout(3000);

        const issues = findHydrationIssues(errors, warnings);

        if (issues.length > 0) {
          console.log(`[FAIL] ${route} hydration errors:`);
          issues.forEach((e) => console.log('  -', e.substring(0, 400)));
        }

        expect(issues, `hydration warnings in ${route}`).toEqual([]);
      });
    }
  });
});


