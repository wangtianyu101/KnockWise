/**
 * V3 PlanCard 组件（PR 1 · V3.0 · 用户已点痛点修复）
 * 4 子卡：当前活跃计划 / 创建按钮 / 历史计划 / 计划详情
 * 视觉：玻璃拟态 + emerald 渐变 + 5 维 mastery radar
 */
import { useState } from 'react';
import { TrophyOutlined, HistoryOutlined, PlusOutlined, EyeOutlined, ReloadOutlined, StopOutlined } from '@ant-design/icons';
import type { StudyPlan, StudyPlanProgress } from '@/types/v3-plan';

// ════════════════════════════════════════════════════════════
// 1. CurrentPlanCard（核心卡 #3 · 5 维 mastery radar + 双进度条）
// ════════════════════════════════════════════════════════════
export function CurrentPlanCard({
  plan,
  onRefresh,
  onViewDetail,
  onEnd,
}: {
  plan: StudyPlan;
  onRefresh?: (planId: string) => void;
  onViewDetail?: (planId: string) => void;
  onEnd?: (planId: string) => void;
}) {
  const progress = plan.progress || { total_target: 0, mastered: 0, learning: 0, new_count: 0, completion_rate: 0, weak_topics_remaining: [] };
  const rate = Math.round(progress.completion_rate * 100);

  return (
    <div
      className="rounded-2xl p-9 border border-emerald-500/30"
      style={{
        background: 'linear-gradient(135deg, rgba(16,185,129,0.12) 0%, rgba(6,182,212,0.12) 100%)',
        boxShadow: '0 12px 40px rgba(16,185,129,0.2)',
      }}
    >
      <div className="flex items-center gap-4 mb-6">
        <div
          className="w-14 h-14 rounded-2xl flex items-center justify-center"
          style={{
            background: 'linear-gradient(135deg, #10b981, #06b6d4)',
            boxShadow: '0 8px 24px rgba(16,185,129,0.4)',
          }}
        >
          <TrophyOutlined style={{ color: 'white', fontSize: 24 }} />
        </div>
        <div>
          <h2 className="text-2xl font-bold mb-1.5" style={{ letterSpacing: '-0.025em' }}>
            当前活跃计划
          </h2>
          <p className="text-base text-emerald-400 font-medium">"{plan.name}"</p>
        </div>
        <button
          className="ml-auto px-4 py-2 rounded-lg text-sm text-gray-300 hover:text-white hover:bg-white/5"
          onClick={() => onViewDetail?.(plan.id)}
        >
          查看详情 →
        </button>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-3 gap-6 mb-6">
        <div className="md:col-span-2">
          <div className="mb-4">
            <div className="flex justify-between mb-2">
              <span className="text-sm text-gray-300">总体进度</span>
              <span className="text-base font-semibold text-emerald-400" style={{ fontFeatureSettings: '"tnum"' }}>
                {progress.mastered} / {progress.total_target}  ·  {rate}%
              </span>
            </div>
            <div className="h-2 rounded-full bg-white/5 overflow-hidden">
              <div
                className="h-full rounded-full transition-all duration-700"
                style={{
                  width: `${rate}%`,
                  background: 'linear-gradient(90deg, #10b981 0%, #06b6d4 100%)',
                }}
              />
            </div>
          </div>
          <div className="flex items-center gap-4 text-sm text-gray-400 mt-4">
            <span>📅 {plan.start_date} ~ {plan.end_date}</span>
            <span>·</span>
            <span>目标：{plan.goal || '未设置'}</span>
            <span>·</span>
            <span className="text-emerald-400">
              弱项：{progress.weak_topics_remaining.length > 0 ? progress.weak_topics_remaining.join(', ') : '[] ✓'}
            </span>
          </div>
        </div>
        <div>
          <p className="text-xs text-gray-500 mb-2 uppercase tracking-wider">5 维掌握度</p>
          <MasteryRadar />
        </div>
      </div>

      <div className="flex gap-3">
        <button
          className="px-4 py-2 rounded-lg text-sm font-medium text-white transition-all"
          style={{ background: 'var(--color-primary)' }}
          onClick={() => onRefresh?.(plan.id)}
        >
          <ReloadOutlined /> 刷新进度
        </button>
        <button
          className="px-4 py-2 rounded-lg text-sm font-medium text-gray-300 bg-white/5 border border-white/10 hover:bg-white/10"
        >
          编辑计划
        </button>
        <button
          className="ml-auto px-4 py-2 rounded-lg text-sm font-medium text-red-400 bg-red-500/10 border border-red-500/20 hover:bg-red-500/20"
          onClick={() => onEnd?.(plan.id)}
        >
          <StopOutlined /> 结束计划
        </button>
      </div>
    </div>
  );
}

// 5 维 mastery radar（mock 雷达图）
function MasteryRadar() {
  return (
    <svg viewBox="0 0 200 160" style={{ width: '100%', height: 'auto' }}>
      <defs>
        <linearGradient id="radar-grad-v3" x1="0" y1="0" x2="0" y2="1">
          <stop offset="0%" stopColor="#10b981" stopOpacity="0.3" />
          <stop offset="100%" stopColor="#10b981" stopOpacity="0.05" />
        </linearGradient>
      </defs>
      <polygon points="100,10 180,55 150,140 50,140 20,55" fill="none" stroke="rgba(148,163,184,0.1)" strokeWidth="1" />
      <polygon points="100,30 160,60 138,125 62,125 40,60" fill="none" stroke="rgba(148,163,184,0.08)" strokeWidth="1" />
      <polygon points="100,50 140,65 125,110 75,110 60,65" fill="none" stroke="rgba(148,163,184,0.06)" strokeWidth="1" />
      <polygon points="100,15 165,58 130,135 55,138 30,60" fill="url(#radar-grad-v3)" stroke="#10b981" strokeWidth="1.5" />
      <circle cx="100" cy="15" r="3" fill="#10b981" />
      <circle cx="165" cy="58" r="3" fill="#10b981" />
      <circle cx="130" cy="135" r="3" fill="#10b981" />
      <circle cx="55" cy="138" r="3" fill="#10b981" />
      <circle cx="30" cy="60" r="3" fill="#10b981" />
      <text x="100" y="6" textAnchor="middle" fill="#94a3b8" fontSize="10">算法</text>
      <text x="188" y="58" textAnchor="start" fill="#94a3b8" fontSize="10">系统</text>
      <text x="158" y="148" textAnchor="start" fill="#94a3b8" fontSize="10">前端</text>
      <text x="42" y="148" textAnchor="end" fill="#94a3b8" fontSize="10">AI</text>
      <text x="12" y="58" textAnchor="end" fill="#94a3b8" fontSize="10">网络</text>
    </svg>
  );
}

// ════════════════════════════════════════════════════════════
// 2. CreatePlanButton（右下浮动 · emerald 主题）
// ════════════════════════════════════════════════════════════
export function CreatePlanButton({ onClick }: { onClick: () => void }) {
  return (
    <button
      onClick={onClick}
      className="fixed bottom-10 right-10 h-[52px] px-[22px] rounded-xl text-sm font-medium text-white inline-flex items-center gap-2 transition-all hover:scale-105"
      style={{
        background: 'var(--color-primary)',
        boxShadow: '0 4px 20px rgba(99,102,241,0.5)',
      }}
    >
      <PlusOutlined /> 创建新计划
    </button>
  );
}

// ════════════════════════════════════════════════════════════
// 3. HistoryPlansList（历史计划列表）
// ════════════════════════════════════════════════════════════
export function HistoryPlansList({
  plans,
  onClick,
}: {
  plans: StudyPlan[];
  onClick: (planId: string) => void;
}) {
  return (
    <div className="rounded-2xl p-7 bg-white/[0.04] border border-white/8">
      <div className="flex items-center gap-2 mb-4">
        <HistoryOutlined className="text-gray-400" />
        <h2 className="text-base font-semibold text-white">历史计划</h2>
        <span className="ml-auto text-xs text-gray-500">{plans.length} 条</span>
      </div>
      {plans.length === 0 ? (
        <div className="text-center text-gray-500 py-6 text-sm">还没有历史计划</div>
      ) : (
        <div className="divide-y divide-white/5">
          {plans.map((plan) => (
            <button
              key={plan.id}
              onClick={() => onClick(plan.id)}
              className="w-full flex items-center justify-between py-3 text-sm text-left hover:bg-white/[0.02] transition-colors"
            >
              <div className="flex items-center gap-3">
                <span
                  className={`text-xs px-2 py-0.5 rounded ${
                    plan.status === 'completed'
                      ? 'bg-emerald-500/15 text-emerald-300'
                      : plan.status === 'paused'
                        ? 'bg-gray-500/15 text-gray-400'
                        : 'bg-indigo-500/15 text-indigo-300'
                  }`}
                >
                  {plan.status === 'completed' ? '已结束' : plan.status === 'paused' ? '已暂停' : '活跃中'}
                </span>
                <span className="text-white">"{plan.name}"</span>
                <span className="text-xs text-gray-500">
                  {plan.start_date} ~ {plan.end_date}
                </span>
              </div>
              <span
                className={
                  plan.status === 'completed'
                    ? 'text-emerald-400 text-xs'
                    : 'text-gray-400 text-xs'
                }
                style={{ fontFeatureSettings: '"tnum"' }}
              >
                ✅ {plan.progress?.mastered || 0} / {plan.progress?.total_target || 0}
              </span>
            </button>
          ))}
        </div>
      )}
    </div>
  );
}

// ════════════════════════════════════════════════════════════
// 4. PlanDetailCard（计划详情 · 点击历史/查看详情 跳转后展示）
// ════════════════════════════════════════════════════════════
export function PlanDetailCard({
  plan,
  onBack,
}: {
  plan: StudyPlan;
  onBack: () => void;
}) {
  return (
    <div className="rounded-2xl p-9 bg-white/[0.04] border border-white/8">
      <div className="flex items-center gap-3 mb-6">
        <button onClick={onBack} className="text-gray-400 hover:text-white">
          ← 返回
        </button>
        <h1 className="text-2xl font-bold">{plan.name}</h1>
        <span
          className={`ml-auto text-xs px-2 py-1 rounded ${
            plan.status === 'active' ? 'bg-emerald-500/20 text-emerald-300' : 'bg-gray-500/15 text-gray-400'
          }`}
        >
          {plan.status}
        </span>
      </div>
      {plan.description && <p className="text-sm text-gray-300 mb-4">{plan.description}</p>}
      {plan.goal && (
        <div className="mb-4">
          <span className="text-xs text-gray-500 uppercase tracking-wider">目标</span>
          <p className="text-base text-white mt-1">{plan.goal}</p>
        </div>
      )}
      <div className="mb-6">
        <span className="text-xs text-gray-500 uppercase tracking-wider">周目标</span>
        <div className="mt-2 space-y-2">
          {plan.weekly_target.map((w) => (
            <div
              key={w.week_idx}
              className="flex items-center justify-between text-sm py-2 px-3 rounded-lg bg-white/[0.02]"
            >
              <span className="text-gray-300">第 {w.week_idx} 周</span>
              <span className="text-emerald-400" style={{ fontFeatureSettings: '"tnum"' }}>
                {w.target_count} 题 · {w.target_topics.join(', ') || '全方向'}
              </span>
            </div>
          ))}
        </div>
      </div>
      <PlanProgressBar progress={plan.progress} />
    </div>
  );
}

function PlanProgressBar({ progress }: { progress?: StudyPlanProgress }) {
  if (!progress) {
    return <div className="text-sm text-gray-500">暂无进度数据</div>;
  }
  const rate = Math.round(progress.completion_rate * 100);
  return (
    <div>
      <div className="flex justify-between mb-2">
        <span className="text-sm text-gray-300">完成度</span>
        <span className="text-base font-semibold text-emerald-400" style={{ fontFeatureSettings: '"tnum"' }}>
          {progress.mastered} / {progress.total_target}  ·  {rate}%
        </span>
      </div>
      <div className="h-2 rounded-full bg-white/5 overflow-hidden">
        <div
          className="h-full rounded-full transition-all duration-700"
          style={{
            width: `${rate}%`,
            background: 'linear-gradient(90deg, #10b981 0%, #06b6d4 100%)',
          }}
        />
      </div>
    </div>
  );
}
