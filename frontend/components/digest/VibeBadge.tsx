"use client";

export type VibeLevel = "info" | "warning" | "empty";

const VIBE_STYLES: Record<VibeLevel, string> = {
  info: "bg-[rgba(99,102,241,0.15)] text-[#c7d2fe] border-[rgba(99,102,241,0.35)]",
  warning: "bg-[rgba(245,158,11,0.15)] text-[#fcd34d] border-[rgba(245,158,11,0.35)]",
  empty: "bg-[rgba(148,163,184,0.06)] text-[#94a3b8] border-[rgba(148,163,184,0.12)]",
};

export function VibeBadge({ vibe, level = "info" }: { vibe: string | null; level?: VibeLevel }) {
  if (!vibe) return null;
  return (
    <span className={`inline-flex items-center gap-1.5 px-3.5 py-1.5 rounded-full text-[13px] font-medium border ${VIBE_STYLES[level]}`}>
      ✨ {vibe}
    </span>
  );
}
