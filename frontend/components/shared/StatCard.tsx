/**
 * StatCard 共享组件 — V1 closure 🟡 #3 抽组件
 *
 * 用法：<StatCard label="已做" value={18} color="indigo" suffix="题" />
 *
 * 用于：dashboard 顶部累计统计 / profile 4 个状态卡（V2 也用）
 */
import React from "react";
import { Card } from "antd";
import GlassCard from "./GlassCard";

interface StatCardProps {
  label: string;
  value: number | string;
  color?: "indigo" | "emerald" | "blue" | "amber";  // text-color class 后缀
  suffix?: string;
  size?: "sm" | "md";  // sm=24px (dashboard), md=36px (profile)
}

const COLOR_CLASSES: Record<NonNullable<StatCardProps["color"]>, string> = {
  indigo: "#a5b4fc",     // 已做
  emerald: "#34d399",    // 已掌握
  blue: "#60a5fa",       // 学习中
  amber: "#fbbf24",      // 连续天数
};

const SIZE_CLASSES = {
  sm: { fontSize: 24 },
  md: { fontSize: 36 },
};

export default function StatCard({
  label,
  value,
  color = "indigo",
  suffix,
  size = "sm",
}: StatCardProps) {
  return (
    <GlassCard variant="default" padding="md">
      <div className="text-center">
        <div style={{ ...SIZE_CLASSES[size], color: COLOR_CLASSES[color] }} className="font-bold font-mono">
          {value}
          {suffix && <span className="text-base ml-1 text-gray-500">{suffix}</span>}
        </div>
        <div className="text-xs text-gray-500 mt-1">{label}</div>
      </div>
    </GlassCard>
  );
}
