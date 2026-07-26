/**
 * ToastProvider smoke test（T1 配套测试 · 4 个非空 assertion · v4 加默认导出 + export-shape）
 *
 * 设计：
 * - mock next/dynamic 避免 vitest/happy-dom 下 ssr:false 报错
 * - 4 个 non-vacuous assertion（对齐 tasks.md § 2 T1 描述）：
 *   1. export-shape（ToastProvider 是函数）
 *   2. 真渲染（render 后 container 存在 sonner-toaster div）
 *   3. position props 透传
 *   4. 默认导出 === named 导出
 *
 * 为什么不用 mixed import（ToastProviderDefault + ToastProvider）：
 * - vitest + vi.mock("next/dynamic", ...) 组合下 mixed import 解析异常
 * - 改用 require() 兜底 · 运行时拿 default export · 与 named export 对比
 */
import React from "react";
import { describe, it, expect, vi } from "vitest";
import { render } from "@testing-library/react";
import { ToastProvider } from "../components/ToastProvider";

// mock next/dynamic：返回 stub 组件 · 接受所有 props · 渲染 data-testid div
vi.mock("next/dynamic", () => ({
  default: () => {
    const StubToaster = (props: Record<string, unknown>) => (
      <div data-testid="sonner-toaster" data-props={JSON.stringify(props)} />
    );
    StubToaster.displayName = "SonnerToaster";
    return StubToaster;
  },
}));

describe("ToastProvider (T1)", () => {
  it("has valid export shape (ToastProvider is a function)", () => {
    // export-shape assertion：named export 必须是函数
    expect(typeof ToastProvider).toBe("function");
    expect(ToastProvider.name).toBe("ToastProvider");
  });

  it("renders without crashing (real DOM render with mocked dynamic)", () => {
    const { container } = render(<ToastProvider position="top-center" />);
    expect(container.firstChild).not.toBeNull();
    expect(container.querySelector('[data-testid="sonner-toaster"]')).not.toBeNull();
  });

  it("forwards position prop to underlying SonnerToaster", () => {
    const { container } = render(<ToastProvider position="bottom-right" />);
    const el = container.querySelector('[data-testid="sonner-toaster"]');
    expect(el).not.toBeNull();
    const dataProps = JSON.parse(el?.getAttribute("data-props") || "{}");
    expect(dataProps.position).toBe("bottom-right");
  });

  it("exposes default export matching the named ToastProvider", async () => {
    // ESM 动态 import 兜底 · 避开 mixed import 在 vitest + vi.mock 下解析异常
    const mod = await import("../components/ToastProvider");
    expect(mod.default).toBeDefined();
    expect(mod.default).toBe(ToastProvider);
  });
});