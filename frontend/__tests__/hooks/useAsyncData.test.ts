/**
 * useAsyncData hook 测试 — V3.8 P2
 * spec §7.3
 */
import { describe, it, expect, vi } from 'vitest';
import { renderHook, act, waitFor } from '@testing-library/react';
import { useAsyncData } from '@/hooks/useAsyncData';

describe('useAsyncData', () => {
  it('fetcher 成功 → data = result · loading=false · error=null', async () => {
    const fetcher = vi.fn().mockResolvedValue({ name: 'ok' });
    const { result } = renderHook(() => useAsyncData(fetcher));

    await waitFor(() => {
      expect(result.current.loading).toBe(false);
    });
    expect(result.current.data).toEqual({ name: 'ok' });
    expect(result.current.error).toBeNull();
  });

  it('fetcher 抛错 → error = Error · loading=false · data=null', async () => {
    const fetcher = vi.fn().mockRejectedValue(new Error('boom'));
    const { result } = renderHook(() => useAsyncData(fetcher));

    await waitFor(() => {
      expect(result.current.loading).toBe(false);
    });
    expect(result.current.error).toBeInstanceOf(Error);
    expect(result.current.error?.message).toBe('boom');
    expect(result.current.data).toBeNull();
  });

  it('初始 loading=true', () => {
    const fetcher = vi.fn().mockResolvedValue('x');
    const { result } = renderHook(() => useAsyncData(fetcher));
    expect(result.current.loading).toBe(true);
  });

  it('reload 重新触发 fetcher', async () => {
    const fetcher = vi.fn().mockResolvedValue('v');
    const { result } = renderHook(() => useAsyncData(fetcher));

    await waitFor(() => expect(result.current.loading).toBe(false));
    expect(fetcher).toHaveBeenCalledTimes(1);

    await act(async () => {
      await result.current.reload();
    });
    expect(fetcher).toHaveBeenCalledTimes(2);
  });

  it('deps 变化重新触发 fetcher', async () => {
    const fetcher = vi.fn().mockResolvedValue('v');
    const { result, rerender } = renderHook(
      ({ id }) => useAsyncData(fetcher, [id]),
      { initialProps: { id: 1 } }
    );

    await waitFor(() => expect(result.current.loading).toBe(false));
    expect(fetcher).toHaveBeenCalledTimes(1);

    rerender({ id: 2 });
    await waitFor(() => expect(fetcher).toHaveBeenCalledTimes(2));
  });

  it('reload 后 error 清除', async () => {
    let shouldFail = true;
    const fetcher = vi.fn().mockImplementation(() => {
      return shouldFail
        ? Promise.reject(new Error('fail'))
        : Promise.resolve('ok');
    });
    const { result } = renderHook(() => useAsyncData(fetcher));

    await waitFor(() => expect(result.current.error).not.toBeNull());

    shouldFail = false;
    await act(async () => {
      await result.current.reload();
    });
    expect(result.current.error).toBeNull();
    expect(result.current.data).toBe('ok');
  });
});