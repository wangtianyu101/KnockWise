/**
 * Playwright 配置 · V3.8 P5
 *
 * 用法：
 *   npx playwright test                    # 跑全部 25 截图测试
 *   npx playwright test --update-snapshots # 更新 baseline（视觉改动后）
 *   npx playwright test dashboard.spec.ts  # 跑单文件
 *
 * 截图 baseline 存 frontend/tests/e2e/__screenshots__/
 * dev server 自动起（webServer 段）
 */
import { defineConfig, devices } from '@playwright/test';

export default defineConfig({
  testDir: './tests/e2e',
  fullyParallel: true,
  forbidOnly: !!process.env.CI,
  retries: 0,
  workers: 1,
  reporter: 'list',

  use: {
    baseURL: 'http://localhost:3000',
    trace: 'retain-on-failure',
    screenshot: 'only-on-failure',
    viewport: { width: 1440, height: 900 },
  },

  projects: [
    {
      name: 'chromium-desktop',
      use: { ...devices['Desktop Chrome'], viewport: { width: 1440, height: 900 } },
    },
    {
      name: 'chromium-mobile',
      use: { ...devices['iPhone 13'] },
      testMatch: /mobile\.spec\.ts$/,
    },
  ],

  // 测试前自动起 dev server（如果端口 3000 没占用）
  webServer: {
    command: 'npm run dev',
    url: 'http://localhost:3000',
    reuseExistingServer: true,
    timeout: 60_000,
    stdout: 'ignore',
    stderr: 'pipe',
  },

  // 截图比对阈值（V3.8 P5 首次 baseline · 用户手动确认）
  // 阈值 0.1% 容许字体抗锯齿/微小像素差
  expect: {
    toHaveScreenshot: { maxDiffPixelRatio: 0.001 },
  },
});