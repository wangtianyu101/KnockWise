import { expect, test } from 'vitest';


test('Vitest blocks unmocked network requests', async () => {
  await expect(fetch('https://example.com/data')).rejects.toThrow(
    'network is disabled in Vitest',
  );
});
