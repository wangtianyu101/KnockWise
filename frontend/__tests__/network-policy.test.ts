import { expect, test } from 'vitest';


test('Vitest blocks unmocked network requests', async () => {
  // vitest 2.x 错误信息格式: "block_external_network (P1-6): Vitest forbids real network. Mock fetch for ... or call (globalThis as any).__allowNetwork__() to override."
  // 用 regex 兼容新老版本错误信息
  await expect(fetch('https://example.com/data')).rejects.toThrow(
    /network is disabled|block_external_network/,
  );
});
