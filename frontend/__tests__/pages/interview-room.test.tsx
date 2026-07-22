/**
 * interview/room.tsx 烟雾测试 — V3.8 P1
 *
 * 目的：Sidebar 全局注入后，interview/room.tsx（最复杂的 page，含 WebSocket + LiveKit）
 * 仍然能 mount 不崩溃。这是 Sidebar 注入安全性的关键 baseline。
 *
 * 不测业务逻辑（WebSocket / 语音），只测：
 * 1. Layout 注入后 render 不抛错
 * 2. 核心 hook 不被破坏
 */
import { describe, it, expect, vi } from 'vitest';
import { render } from '@testing-library/react';

vi.mock('next/router', () => ({
  useRouter: () => ({
    push: vi.fn(),
    replace: vi.fn(),
    pathname: '/interview/room',
    query: { id: 'test-interview-id' },
    asPath: '/interview/room?id=test-interview-id',
    isReady: true,
  }),
}));

// Mock fetch 全局（避免真实 API 调用）
global.fetch = vi.fn().mockResolvedValue({
  ok: true,
  json: async () => ({ id: 'test-interview-id', status: 'ready' }),
});

// Mock WebSocket（避免真实连接）
class MockWebSocket {
  onopen: any = null;
  onmessage: any = null;
  onclose: any = null;
  onerror: any = null;
  constructor(public url: string) {}
  send() {}
  close() {}
}
(global as any).WebSocket = MockWebSocket;

// Mock LiveKit 组件（避免真实依赖）
vi.mock('@/components/InterviewerAvatar', () => ({
  default: () => <div data-testid="mock-avatar" />,
}));
vi.mock('@/components/LiveTranscript', () => ({
  default: () => <div data-testid="mock-transcript" />,
}));
vi.mock('@/components/VoiceRecord', () => ({
  default: () => <div data-testid="mock-voice" />,
}));

// 在 _app.tsx 注入 Layout 后，interview/room.tsx 是 Layout 的 child
// 这里我们手动模拟 _app.tsx 的包装
import { Layout } from '@/components/v3/Layout/Layout';
import InterviewRoom from '@/pages/interview/room';

describe('interview/room.tsx 在 Layout 包裹下的烟雾测试', () => {
  it('Sidebar + Layout + InterviewRoom 一起 render 不报错', () => {
    expect(() => {
      render(
        <Layout currentPage="/interview/room">
          <InterviewRoom />
        </Layout>
      );
    }).not.toThrow();
  });

  it('Sidebar 仍能渲染（即使在 interview/room 中）', () => {
    const { getByTestId } = render(
      <Layout currentPage="/interview/room">
        <InterviewRoom />
      </Layout>
    );
    expect(getByTestId('sidebar')).toBeInTheDocument();
    expect(getByTestId('topnav')).toBeInTheDocument();
  });
});