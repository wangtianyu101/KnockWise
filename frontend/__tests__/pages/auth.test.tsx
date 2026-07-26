/**
 * auth.test.tsx — T7 前端 auth 综合测试
 *
 * 端到端 mock 测试 pages/auth.tsx 行为：
 * - onBlur 调 check-email → 自动切登录/注册态（决策 10）
 * - 提交调 authenticate → mode 字段决定 toast 文案（v5 决策 13）
 * - 500ms 后 router.push('/dashboard')（AC-1）
 * - 失败 toast.error + 不跳转
 * - v4 UI 验收：卡片只有标题（无副标题/无检查状态指示器/brand-block 无 tagline/默认按钮"登录 / 注册"）
 */
import React from "react";
import { describe, it, expect, vi, beforeEach } from "vitest";
import { render, screen, fireEvent, waitFor, act } from "@testing-library/react";

// Hoist mocks（必须在 import 之前）
const mockRouter = vi.hoisted(() => ({
  push: vi.fn(),
  replace: vi.fn(),
  pathname: "/auth",
  query: {},
  asPath: "/auth",
}));

const mockAuthenticate = vi.hoisted(() => vi.fn());

const mockToast = vi.hoisted(() => ({
  success: vi.fn(),
  error: vi.fn(),
}));

vi.mock("next/router", () => ({
  useRouter: () => mockRouter,
}));

vi.mock("@/lib/api", () => ({
  authenticate: mockAuthenticate,
  getToken: () => null,
  setToken: vi.fn(),
  clearToken: vi.fn(),
}));

vi.mock("sonner", () => ({
  toast: mockToast,
}));

import Auth from "../../pages/auth";

describe("Auth page (T7 · 决策 10/11/12/13)", () => {
  beforeEach(() => {
    mockRouter.push.mockClear();
    mockRouter.replace.mockClear();
    mockAuthenticate.mockClear();
    mockToast.success.mockClear();
    mockToast.error.mockClear();
    // 默认 fetch 返回 200 (exists=false) for check-email
    global.fetch = vi.fn(() =>
      Promise.resolve({
        ok: true,
        status: 200,
        json: () => Promise.resolve({ exists: false, email: "user@example.com" }),
      } as Response)
    ) as unknown as typeof fetch;
  });

  // ── onBlur 自动判断（决策 10） ─────────────────────────

  it("默认态显示：欢迎来到 KnockWise + 登录 / 注册按钮", () => {
    render(<Auth />);
    expect(screen.getByText("欢迎来到 KnockWise")).toBeInTheDocument();
    expect(screen.getByRole("button", { name: /登录 \/ 注册/ })).toBeInTheDocument();
  });

  it("onBlur 调 check-email（exists=false）→ 切注册态", async () => {
    global.fetch = vi.fn(() =>
      Promise.resolve({
        ok: true,
        json: () => Promise.resolve({ exists: false, email: "new@example.com" }),
      } as Response)
    ) as unknown as typeof fetch;

    render(<Auth />);
    const emailInput = screen.getByPlaceholderText("wangtianyu@example.com");
    fireEvent.change(emailInput, { target: { value: "new@example.com" } });
    fireEvent.blur(emailInput);

    await waitFor(() => {
      expect(screen.getByText("加入 KnockWise")).toBeInTheDocument();
    });
    expect(screen.getByRole("button", { name: /注 册/ })).toBeInTheDocument();
  });

  it("onBlur 调 check-email（exists=true）→ 切登录态 + 邮箱 readonly", async () => {
    global.fetch = vi.fn(() =>
      Promise.resolve({
        ok: true,
        json: () => Promise.resolve({ exists: true, email: "wangtianyu@example.com" }),
      } as Response)
    ) as unknown as typeof fetch;

    render(<Auth />);
    const emailInput = screen.getByPlaceholderText("wangtianyu@example.com");
    fireEvent.change(emailInput, { target: { value: "wangtianyu@example.com" } });
    fireEvent.blur(emailInput);

    await waitFor(() => {
      expect(screen.getByText("欢迎回来")).toBeInTheDocument();
    });
    expect(screen.getByRole("button", { name: /登 录/ })).toBeInTheDocument();
    // 邮箱 readonly
    expect(emailInput).toHaveAttribute("readonly");
  });

  it("onBlur 时邮箱格式错（无 @）→ 不调 check-email + 状态不变", () => {
    const fetchSpy = vi.fn();
    global.fetch = fetchSpy as unknown as typeof fetch;
    render(<Auth />);
    const emailInput = screen.getByPlaceholderText("wangtianyu@example.com");
    fireEvent.change(emailInput, { target: { value: "no-at-sign" } });
    fireEvent.blur(emailInput);
    expect(fetchSpy).not.toHaveBeenCalled();
    // 仍在默认态
    expect(screen.getByText("欢迎来到 KnockWise")).toBeInTheDocument();
  });

  // ── 注册态提交流程（AC-1 happy path） ─────────────────────

  it("注册态提交 → 调 authenticate(email, password, display_name) + toast.success + router.push", async () => {
    global.fetch = vi.fn(() =>
      Promise.resolve({
        ok: true,
        json: () => Promise.resolve({ exists: false, email: "newuser@example.com" }),
      } as Response)
    ) as unknown as typeof fetch;
    mockAuthenticate.mockResolvedValue({
      access_token: "eyJ...",
      token_type: "bearer",
      user: { id: "42", email: "newuser@example.com", display_name: "新用户" },
      mode: "register",
    });

    render(<Auth />);
    const emailInput = screen.getByPlaceholderText("wangtianyu@example.com");
    const passwordInput = screen.getByPlaceholderText("••••••");

    fireEvent.change(emailInput, { target: { value: "newuser@example.com" } });
    fireEvent.blur(emailInput);
    await waitFor(() => screen.getByText("加入 KnockWise"));

    const displayNameInput = screen.getByPlaceholderText("你的昵称");
    fireEvent.change(displayNameInput, { target: { value: "新用户" } });
    fireEvent.change(passwordInput, { target: { value: "123456" } });

    await act(async () => {
      fireEvent.click(screen.getByRole("button", { name: /注 册/ }));
      // 跳过 500ms setTimeout（用 vi.useFakeTimers 不必要 · 直接等回调）
      await new Promise((r) => setTimeout(r, 600));
    });

    expect(mockAuthenticate).toHaveBeenCalledWith(
      "newuser@example.com",
      "123456",
      "新用户"
    );
    expect(mockToast.success).toHaveBeenCalledWith(
      expect.stringContaining("创建成功")
    );
    expect(mockRouter.push).toHaveBeenCalledWith("/dashboard");
  });

  // ── 登录态提交流程（AC-1 happy path · mode=login） ────────

  it("登录态提交 → 调 authenticate（不传 display_name）+ toast.success + router.push", async () => {
    global.fetch = vi.fn(() =>
      Promise.resolve({
        ok: true,
        json: () => Promise.resolve({ exists: true, email: "wangtianyu@example.com" }),
      } as Response)
    ) as unknown as typeof fetch;
    mockAuthenticate.mockResolvedValue({
      access_token: "eyJ...",
      token_type: "bearer",
      user: { id: "1", email: "wangtianyu@example.com", display_name: "wangtianyu" },
      mode: "login",
    });

    render(<Auth />);
    const emailInput = screen.getByPlaceholderText("wangtianyu@example.com");
    const passwordInput = screen.getByPlaceholderText("••••••");

    fireEvent.change(emailInput, { target: { value: "wangtianyu@example.com" } });
    fireEvent.blur(emailInput);
    await waitFor(() => screen.getByText("欢迎回来"));

    fireEvent.change(passwordInput, { target: { value: "123456" } });

    await act(async () => {
      fireEvent.click(screen.getByRole("button", { name: /登 录/ }));
      await new Promise((r) => setTimeout(r, 600));
    });

    expect(mockAuthenticate).toHaveBeenCalledWith(
      "wangtianyu@example.com",
      "123456",
      undefined  // 登录态不传 display_name
    );
    expect(mockToast.success).toHaveBeenCalledWith(
      expect.stringContaining("登录成功")
    );
    expect(mockRouter.push).toHaveBeenCalledWith("/dashboard");
  });

  // ── 失败流程（AC-1 failure） ─────────────────────────────

  it("提交失败 → toast.error + 不跳转", async () => {
    mockAuthenticate.mockRejectedValue(new Error("邮箱或密码错误"));

    render(<Auth />);
    const emailInput = screen.getByPlaceholderText("wangtianyu@example.com");
    const passwordInput = screen.getByPlaceholderText("••••••");
    fireEvent.change(emailInput, { target: { value: "user@example.com" } });
    fireEvent.change(passwordInput, { target: { value: "123456" } });  // ≥ 6 位避免 HTML5 minLength validation 阻止 submit

    fireEvent.click(screen.getByRole("button", { name: /登录 \/ 注册/ }));

    await waitFor(() => {
      expect(mockToast.error).toHaveBeenCalledWith("邮箱或密码错误");
    });
    expect(mockRouter.push).not.toHaveBeenCalled();
    expect(mockToast.success).not.toHaveBeenCalled();
  });

  // ── v4 UI 验收（决策 12） ─────────────────────────────────

  it("v4 UI 精简：卡片只有标题（无副标题 / 无检查状态指示器）", () => {
    render(<Auth />);
    // 无 subtitle / subheading
    expect(screen.queryByText(/输入邮箱/)).not.toBeInTheDocument();
    expect(screen.queryByText(/我们会自动判断/)).not.toBeInTheDocument();
    // 无 check-status indicator
    expect(document.querySelector(".check-status")).toBeNull();
  });

  it("v4 UI 精简：brand-block 无 tagline（无'智能面试 · 真正会追问'）", () => {
    render(<Auth />);
    expect(screen.queryByText(/智能面试/)).not.toBeInTheDocument();
    expect(screen.queryByText(/真正会追问/)).not.toBeInTheDocument();
  });

  it("Logo 是 V3 K logo SVG（不是 ⚡ 字符 / 不是 Mail 图标）", () => {
    render(<Auth />);
    const logo = document.querySelector(".w-14 svg");
    expect(logo).toBeInTheDocument();
    // SVG path d="M9 7v14M9 21l11-14" (V3 K logo 特征)
    const path = logo?.querySelector("path");
    expect(path?.getAttribute("d")).toContain("M9 7v14");
  });

  it("默认按钮文字 = '登录 / 注册'（不是'继续'也不是 disabled）", () => {
    render(<Auth />);
    const button = screen.getByRole("button", { name: /登录 \/ 注册/ });
    expect(button).not.toBeDisabled();
  });

  // ── 边界 ──────────────────────────────────────────────

  it("onBlur 调 check-email（400 invalid email）→ 状态不变（不切）", async () => {
    global.fetch = vi.fn(() =>
      Promise.resolve({
        ok: false,
        status: 400,
        json: () => Promise.resolve({ detail: "Invalid email" }),
      } as Response)
    ) as unknown as typeof fetch;

    render(<Auth />);
    const emailInput = screen.getByPlaceholderText("wangtianyu@example.com");
    fireEvent.change(emailInput, { target: { value: "wangtianyu@" } });
    fireEvent.blur(emailInput);

    await new Promise((r) => setTimeout(r, 100));
    // 仍在默认态
    expect(screen.getByText("欢迎来到 KnockWise")).toBeInTheDocument();
  });

  it("onBlur 调 check-email 失败（网络错误）→ 静默处理（不切状态）", async () => {
    global.fetch = vi.fn(() => Promise.reject(new Error("Network error"))) as unknown as typeof fetch;

    render(<Auth />);
    const emailInput = screen.getByPlaceholderText("wangtianyu@example.com");
    fireEvent.change(emailInput, { target: { value: "user@example.com" } });
    fireEvent.blur(emailInput);

    await new Promise((r) => setTimeout(r, 100));
    // 仍在默认态（不报错）
    expect(screen.getByText("欢迎来到 KnockWise")).toBeInTheDocument();
    expect(mockToast.error).not.toHaveBeenCalled();
  });
});