/**
 * GlassCard 共享组件 — V1 closure 🟡 #1 抽组件
 *
 * 用法：<GlassCard>...</GlassCard> 替代重复的卡片 div
 * Props:
 * - variant: "default" | "hover-lift"（dashboard 模块卡 hover 上升效果）
 * - padding: "sm" | "md"（默认 md=p-7）
 * - onClick: 可选，变成可点击卡片
 * - data-testid: 测试用，传递到最外层 div
 */
import React from "react";

interface GlassCardProps {
  children: React.ReactNode;
  className?: string;
  variant?: "default" | "hover-lift";
  padding?: "sm" | "md";
  onClick?: () => void;
  /** 测试用，透传到最外层 div */
  "data-testid"?: string;
  /** 类型安全的 HTML tag（默认 div） */
  as?: "div" | "section" | "article";
}

const BASE = "bg-white/[0.03] backdrop-blur-xl border border-indigo-500/10 rounded-2xl";

const VARIANTS = {
  default: "",
  "hover-lift":
    "cursor-pointer hover:border-indigo-500/30 hover:-translate-y-1 transition-all duration-300 overflow-hidden",
} as const;

const PADDINGS = {
  sm: "p-4",
  md: "p-7",
} as const;

export default function GlassCard({
  children,
  className = "",
  variant = "default",
  padding = "md",
  onClick,
  as = "div",
  "data-testid": testId,
}: GlassCardProps) {
  const cls = `${BASE} ${VARIANTS[variant]} ${PADDINGS[padding]} ${className}`.trim();
  if (as === "section") return <section onClick={onClick} data-testid={testId} className={cls}>{children}</section>;
  if (as === "article") return <article onClick={onClick} data-testid={testId} className={cls}>{children}</article>;
  return <div onClick={onClick} data-testid={testId} className={cls}>{children}</div>;
}
