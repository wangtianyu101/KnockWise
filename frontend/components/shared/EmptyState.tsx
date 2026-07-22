/**
 * EmptyState 共享组件 — V1 closure 🟡 #4（5.3.4 空状态占位图升级）
 * 之前：antd `<Empty />` 简单占位，无插画 + 无 CTA
 * 现在：4 种 type 插画 (knowledge | progress | data | vault) + 标题 + 描述 + 可选 CTA
 *
 * 用法：
 *   <EmptyState type="knowledge" title="暂无笔记" description="答 3 道题后..." />
 *   <EmptyState type="progress" title="今天没学习" ctaText="开始学习" onCta={...} />
 */
import type { JSX } from "react"; // 2026-07-22 audit 修复 · React 19 JSX namespace 不在全局
import React from "react";

type EmptyType = "knowledge" | "progress" | "data" | "vault";

interface EmptyStateProps {
  /** 空状态类型（4 种预设插画） */
  type: EmptyType;
  /** 标题（默认显示） */
  title: string;
  /** 描述（可选） */
  description?: string;
  /** CTA 按钮文字（可选） */
  ctaText?: string;
  /** CTA 点击回调 */
  onCta?: () => void;
  /** 测试用 */
  "data-testid"?: string;
}

const ICONS: Record<EmptyType, JSX.Element> = {
  knowledge: (
    <svg
      width="56"
      height="56"
      viewBox="0 0 56 56"
      fill="none"
      xmlns="http://www.w3.org/2000/svg"
      data-testid="empty-icon-knowledge"
    >
      {/* 笔记本 SVG（紫色渐变） */}
      <rect
        x="12"
        y="10"
        width="32"
        height="38"
        rx="3"
        stroke="url(#g1)"
        strokeWidth="2"
      />
      <line x1="18" y1="20" x2="38" y2="20" stroke="#a78bfa" strokeWidth="1.5" />
      <line x1="18" y1="28" x2="38" y2="28" stroke="#a78bfa" strokeWidth="1.5" />
      <line x1="18" y1="36" x2="32" y2="36" stroke="#a78bfa" strokeWidth="1.5" />
      <defs>
        <linearGradient id="g1" x1="0%" y1="0%" x2="100%" y2="100%">
          <stop offset="0%" stopColor="#a78bfa" />
          <stop offset="100%" stopColor="#6366f1" />
        </linearGradient>
      </defs>
    </svg>
  ),
  progress: (
    <svg
      width="56"
      height="56"
      viewBox="0 0 56 56"
      fill="none"
      xmlns="http://www.w3.org/2000/svg"
      data-testid="empty-icon-progress"
    >
      {/* 圆形进度图 SVG（绿色渐变） */}
      <circle cx="28" cy="28" r="20" stroke="#34d39933" strokeWidth="4" />
      <path
        d="M28 8a20 20 0 0 1 14 34"
        stroke="#34d399"
        strokeWidth="4"
        strokeLinecap="round"
      />
    </svg>
  ),
  data: (
    <svg
      width="56"
      height="56"
      viewBox="0 0 56 56"
      fill="none"
      xmlns="http://www.w3.org/2000/svg"
      data-testid="empty-icon-data"
    >
      {/* 数据条 SVG（蓝色渐变） */}
      <line x1="16" y1="40" x2="16" y2="28" stroke="#60a5fa" strokeWidth="3" strokeLinecap="round" />
      <line x1="28" y1="40" x2="28" y2="22" stroke="#60a5fa" strokeWidth="3" strokeLinecap="round" />
      <line x1="40" y1="40" x2="40" y2="14" stroke="#60a5fa" strokeWidth="3" strokeLinecap="round" />
      <line x1="12" y1="44" x2="44" y2="44" stroke="#60a5fa55" strokeWidth="2" />
    </svg>
  ),
  vault: (
    <svg
      width="56"
      height="56"
      viewBox="0 0 56 56"
      fill="none"
      xmlns="http://www.w3.org/2000/svg"
      data-testid="empty-icon-vault"
    >
      {/* Vault 锁 SVG（amber 渐变） */}
      <rect
        x="14"
        y="22"
        width="28"
        height="22"
        rx="3"
        stroke="#fbbf24"
        strokeWidth="2"
      />
      <path
        d="M20 22v-4a8 8 0 0 1 16 0v4"
        stroke="#fbbf24"
        strokeWidth="2"
        fill="none"
      />
      <circle cx="28" cy="32" r="2" fill="#fbbf24" />
    </svg>
  ),
};

export default function EmptyState({
  type,
  title,
  description,
  ctaText,
  onCta,
  "data-testid": testId,
}: EmptyStateProps) {
  return (
    <div
      data-testid={testId ?? `empty-${type}`}
      className="flex flex-col items-center justify-center py-12 px-6 text-center"
    >
      <div className="opacity-60 mb-4">{ICONS[type]}</div>
      <h3 className="text-base font-medium text-gray-300 mb-1">{title}</h3>
      {description && (
        <p className="text-sm text-gray-500 max-w-sm mb-4">{description}</p>
      )}
      {ctaText && onCta && (
        <button
          onClick={onCta}
          className="px-4 py-2 rounded-lg bg-indigo-500/20 text-indigo-300 hover:bg-indigo-500/30 transition-colors text-sm font-medium"
        >
          {ctaText}
        </button>
      )}
    </div>
  );
}
