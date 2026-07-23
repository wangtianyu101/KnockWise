import '@testing-library/jest-dom/vitest';
import { vi, beforeEach, afterEach } from 'vitest';

// P1-6: block_external_network — 默认拦截真网络请求
// 单测需要真网络时显式声明 (globalThis as any).__allowNetwork__() 即可
const _realFetch = globalThis.fetch
let _networkAllowed = false

beforeEach(() => {
  _networkAllowed = false
  globalThis.fetch = vi.fn(async (input: RequestInfo | URL) => {
    if (_networkAllowed) return _realFetch(input as any)
    throw new Error(
      `block_external_network (P1-6): Vitest forbids real network. ` +
      `Mock fetch for ${String(input)} or call (globalThis as any).__allowNetwork__() to override.`
    )
  }) as any
})

afterEach(() => {
  globalThis.fetch = _realFetch
})

;(globalThis as any).__allowNetwork__ = () => {
  _networkAllowed = true
}

// Mock Next.js router (避免引入 next/router 真实模块)
vi.mock('next/router', () => ({
  useRouter: () => ({
    push: vi.fn(),
    replace: vi.fn(),
    pathname: '/',
    query: {},
    asPath: '/',
  }),
}));

// Mock API token (避免 localStorage 在 happy-dom 里报错)
vi.mock('@/lib/api', () => ({
  getToken: vi.fn(() => 'mock-token'),
  clearToken: vi.fn(),
  setToken: vi.fn(),
  getProfile: vi.fn(),
  updateProfile: vi.fn(),
  uploadResume: vi.fn(),
  deleteResume: vi.fn(),
  startInterview: vi.fn(),
  getNextQuestion: vi.fn(),
  submitAnswer: vi.fn(),
  getReport: vi.fn(),
  generateReport: vi.fn(),
}));
