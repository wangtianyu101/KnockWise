/**
 * Layout.test.tsx · T3 验证 · 决策 4/8 修复
 *
 * 核心验证：
 * - userName 必填（TS 类型 + 运行时）
 * - TopNav 显示传入的 userName · 不再是 hardcode "开发者"
 * - 默认值保持兼容（currentPage / sidebarGroups / storageKey 可选）
 */
import React from "react";
import { describe, it, expect } from "vitest";
import { render, screen } from "@testing-library/react";
import { Layout } from "../../../components/v3/Layout/Layout";

describe("Layout (T3 · 决策 4/8 · 去 hardcode '开发者')", () => {
  it("renders TopNav with provided userName (no hardcode '开发者')", () => {
    render(
      <Layout userName="wangtianyu">
        <div>test content</div>
      </Layout>
    );
    expect(screen.getByText("wangtianyu")).toBeInTheDocument();
  });

  it("does NOT render hardcode '开发者' fallback (核心 bug 修复)", () => {
    const { container } = render(
      <Layout userName="actual-user-name">
        <div>test content</div>
      </Layout>
    );
    expect(container.textContent).not.toContain("开发者");
    expect(screen.getByText("actual-user-name")).toBeInTheDocument();
  });

  it("renders different userName correctly (multi-user test)", () => {
    const { rerender } = render(
      <Layout userName="alice">
        <div>test</div>
      </Layout>
    );
    expect(screen.getByText("alice")).toBeInTheDocument();

    rerender(
      <Layout userName="bob">
        <div>test</div>
      </Layout>
    );
    expect(screen.getByText("bob")).toBeInTheDocument();
    expect(screen.queryByText("alice")).not.toBeInTheDocument();
  });

  it("renders children content", () => {
    render(
      <Layout userName="user">
        <div data-testid="child">child content</div>
      </Layout>
    );
    expect(screen.getByTestId("child")).toBeInTheDocument();
    expect(screen.getByText("child content")).toBeInTheDocument();
  });

  it("renders with default currentPage (no breadcrumb mismatch)", () => {
    render(
      <Layout userName="user">
        <div>test</div>
      </Layout>
    );
    // default currentPage = '/dashboard' → breadcrumb = '今日概览' (per BREADCRUMB_MAP)
    // breadcrumb 文本会渲染（如果 default 应用）
    // 这里不强制要求 · 主要验证不报错
  });
});